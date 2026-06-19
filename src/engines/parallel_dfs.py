import multiprocessing
import queue
import time
from typing import List, Set, Tuple, Dict
from src.core.graph import Multigraph
from src.core.models import TransitEdge
from src.concurrency.thread_safe_pool import ThreadSafeSolutionPool, ThreadSafeDominanceFrontier
from src.concurrency.work_stealing import WorkStealingManager

def find_alternative_paths(
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,    
    max_transfers: int  
) -> List[List[TransitEdge]]:
    """
    Sequential Baseline Engine using Depth-First Search.
    Discovers all non-cyclic feasible paths respecting constraints.
    """
    all_valid_paths: List[List[TransitEdge]] = []
    dominance_frontier: Dict[str, Tuple[float, int]] = {}

    def dfs_worker(
        current_node: str,
        current_path: List[TransitEdge],
        visited_nodes: Set[str],
        accumulated_time: float,
        accumulated_transfers: int
    ):
        if accumulated_time > max_time or accumulated_transfers > max_transfers:
            return
        
        if current_node in dominance_frontier:
            best_time, best_transfers = dominance_frontier[current_node]
            if accumulated_time >= best_time and accumulated_transfers >= best_transfers:
                return
            
        dominance_frontier[current_node] = (accumulated_time, accumulated_transfers)
             
        if current_node == end:
            all_valid_paths.append(list(current_path))
            return
        
        for edge in graph.get_neighbors(current_node):
            if edge.v not in visited_nodes: 
                visited_nodes.add(edge.v)
                current_path.append(edge)

                next_time = accumulated_time + edge.time 
                next_transfers = accumulated_transfers + edge.transfer 

                dfs_worker(edge.v, current_path, visited_nodes, next_time, next_transfers)
                
                current_path.pop()
                visited_nodes.remove(edge.v)

    initial_visited = {start}
    dfs_worker(start, [], initial_visited, 0.0, 0)
    return all_valid_paths

def parallel_worker_loop(
    worker_id: int,
    num_workers: int,
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,
    max_transfers: int,
    signal_queues: Dict[int, any],
    work_queues: Dict[int, any],     
    solution_pool: ThreadSafeSolutionPool,
    worker_states: any
) -> None:
    """
    Asynchronous Worker Processing Loop leveraging an atomic global pruning frontier and decentralized dynamic load balancing via Work Stealing.
    """
    local_frontier: Dict[str, Tuple[float, int]] = {}
    local_stack: List[Tuple[str, float, int, List[TransitEdge], frozenset]] = []

    try: 
        boot_task = work_queues[worker_id].get(timeout=0.01)
        node, curr_time, curr_transfers, path = boot_task
        local_stack.append((node, curr_time, curr_transfers, path, frozenset([start])))
        worker_states[worker_id] = 1
    except queue.Empty: 
        worker_states[worker_id] = 0
    
    while True:
        if not local_stack: 
            worker_states[worker_id] = 0

            if sum(worker_states) == 0:
                break

            while not work_queues[worker_id].empty():
                try:
                    work_queues[worker_id].get_nowait()
                except queue.Empty:
                    break

            stolen_frame = None
            for target_id in range(num_workers):
                if target_id == worker_id:
                    continue
                
                if worker_states[target_id] == 1:
                    try:
                        signal_queues[target_id].put_nowait(worker_id)
                        stolen_frame = work_queues[worker_id].get(timeout=0.01)
                        if stolen_frame:
                            break
                    except (queue.Empty, queue.Full):
                        continue

            if stolen_frame:
                worker_states[worker_id] = 1 
                node, t_val, tr_val, path_hist = stolen_frame
                v_set = frozenset([start] + [e.v for e in path_hist])
                local_stack.append((node, t_val, tr_val, path_hist, v_set))
                continue
            else:
                if sum(worker_states) == 0:
                    break
                time.sleep(0.002)
                continue
        
        current_node, curr_time, curr_transfers, path, visited_nodes = local_stack.pop()

        if current_node == end:
            solution_pool.add_solution(list(path))
            continue

        if not signal_queues[worker_id].empty():
            try:
                thief_id = signal_queues[worker_id].get_nowait()
                
                temp_4element_stack = [(n, t, tr, p) for (n, t, tr, p, v) in local_stack]
                stolen_packet = WorkStealingManager.split_stack(temp_4element_stack)

                if stolen_packet:
                    local_stack.pop(0) 
                    work_queues[thief_id].put_nowait(stolen_packet)
                    
            except (queue.Empty, queue.Full):
                pass

        for edge in graph.get_neighbors(current_node): 
            if edge.v in visited_nodes:
                continue

            next_time = curr_time + edge.time
            next_transfers = curr_transfers + edge.transfer

            if next_time > max_time or next_transfers > max_transfers:
                continue

            # Check local frontier for this worker
            if edge.v in local_frontier:
                best_time, best_transfers = local_frontier[edge.v]
                if next_time >= best_time and next_transfers >= best_transfers:
                    continue
            
            # Update local frontier
            local_frontier[edge.v] = (next_time, next_transfers)

            next_path = path + [edge]
            next_visited = visited_nodes | frozenset([edge.v])
            local_stack.append((edge.v, next_time, next_transfers, next_path, next_visited))
    
    worker_states[worker_id] = 0


def find_paths_parallel(
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,
    max_transfers: int,
    num_workers: int    
) -> List[List[TransitEdge]]:
    with multiprocessing.Manager() as central_manager:
        solution_pool = ThreadSafeSolutionPool(central_manager) 

        signal_queues = {i: central_manager.Queue() for i in range(num_workers)}
        work_queues = {i: central_manager.Queue() for i in range(num_workers)}
        worker_states = multiprocessing.Array('i', [1] * num_workers)

        work_queues[0].put((start, 0.0, 0, []))
        processes = []

        for worker_id in range(num_workers):
            p = multiprocessing.Process(
                target=parallel_worker_loop,
                args=(
                    worker_id,
                    num_workers,
                    graph,
                    start,
                    end,
                    max_time,
                    max_transfers,
                    signal_queues,
                    work_queues,
                    solution_pool,
                    worker_states
                )
            )
            processes.append(p)
            p.start()

        for p in processes:
            p.join()

        raw_parallel_solutions = [list(path) for path in solution_pool.get_all_solutions()]

    # Deduplicate paths (work stealing overlaps can occasionally result in identical paths being discovered twice)
    unique_paths = []
    seen_signatures = set()
    
    for path in raw_parallel_solutions:
        signature = tuple([edge.v for edge in path])
        if signature not in seen_signatures:
            seen_signatures.add(signature)
            unique_paths.append(path)

    return unique_paths