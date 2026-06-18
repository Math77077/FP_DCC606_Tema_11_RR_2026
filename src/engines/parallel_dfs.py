import multiprocessing
import queue
import time
from typing import List, Set, Tuple, Dict
from multiprocessing.sharedctypes import Synchronized
from src.core.graph import Multigraph
from src.core.models import TransitEdge
from src.concurrency.thread_safe_pool import ThreadSafeSolutionPool
from src.concurrency.work_stealing import WorkStealingManager

def find_alternative_paths(
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,    # Maximum allowed travel time (t_max)
    max_transfers: int  # Maximum allowed line transfers (tr_max)
) -> List[List[TransitEdge]]:
    all_valid_paths: List[List[TransitEdge]] = []

    def dfs_worker(
        current_node: str,
        current_path: List[TransitEdge],
        visited_nodes: Set[str],
        accumulated_time: float,
        accumulated_transfers: int
    ):
        # This is our constraints to limit our exploration
        if accumulated_time > max_time:
            return
        if accumulated_transfers > max_transfers:
            return
        
        # The condition that tells us if we have successfully reached our final 'end' node        
        if current_node == end:
            all_valid_paths.append(list(current_path))
            return
        
        for edge in graph.get_neighbors(current_node):
            # This is to avoid infinite loops, avoid checking a place we already have visited
            if edge.v not in visited_nodes: # If our destination node is not on visited_nodes
                
                # We add the destination into our visited list and add to our current path
                visited_nodes.add(edge.v)
                current_path.append(edge)

                # We are calculating the next costs as we progress
                next_time = accumulated_time + edge.time # New time needed
                next_transfers = accumulated_transfers + edge.transfer # new number of transfers needed

                # After calculating and adding the new values for our current_node,
                # we progress the search. In other words, we go forward to the next
                # node, which is the destination (edge.v), while passing the values
                # we have accumulated so far
                dfs_worker(edge.v, current_path, visited_nodes, next_time, next_transfers)
                
                # Now we clean up our workstation.
                # We have to clean it up, because when other paths uses this
                # function, the function shouldnt have the values of the previous paths tested.
                # They have to use the new paths to fill these elements below with new information,
                # new valid paths
                current_path.pop()
                visited_nodes.remove(edge.v)

    # To make the search start at the beginning node
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
    work_queues: Dict[int, any],     # This is the dictionary containing all worker queues
    solution_pool: ThreadSafeSolutionPool,
    active_workers: Synchronized
) -> None:
    # frame template: (current_node, accumulated_time, accumulated_transfers, path_list)
    local_stack: List[Tuple[str, float, int, List[TransitEdge]]] = []

    try: # grap initial task to start the worker's engine
        boot_task = work_queues[worker_id].get(timeout=0.05)
        current_node, curr_time, curr_transfers, path = boot_task
        local_stack.append((current_node, curr_time, curr_transfers, path))
    except queue.Empty: # in case of empty queue, we exit early
        with active_workers.get_lock():
            active_workers.value -= 1
    
    while True:
        if not local_stack:
            with active_workers.get_lock():
                if active_workers.value <= 0:
                    break

            with active_workers.get_lock():
                active_workers.value -= 1

            stolen_frame = None

            for target_id in range(num_workers):
                if target_id == worker_id:
                    continue

                try:
                    signal_queues[target_id].put_nowait(worker_id)
                    stolen_frame = work_queues[worker_id].get(timeout=0.02)
                    if stolen_frame:
                        break
                except (queue.Empty, queue.Full):
                    continue

            if stolen_frame:
                with active_workers.get_lock():
                    active_workers.value += 1
                local_stack.append(stolen_frame)
                continue
            else:
                with active_workers.get_lock():
                    if active_workers.value <= 0:
                        break
                        
                time.sleep(0.002)
                continue

        current_node, curr_time, curr_transfers, path = local_stack.pop()

        if current_node == end:
            solution_pool.add_solution(path)
            continue

        # checking if our own queue to verify if another worker pushed their ID inside it
        if not signal_queues[worker_id].empty():
            try:
                thief_id = signal_queues[worker_id].get_nowait()
                stolen_packet = WorkStealingManager.split_stack(local_stack)

                if stolen_packet:
                    work_queues[thief_id].put_nowait(stolen_packet)
            except (queue.Empty, queue.Full):
                pass

        for edge in graph.get_neighbors(current_node): 
            if edge.v == start or any(p.v == edge.v for p in path): # cycle detection, avoid redundancy
                continue

            # accumulate the constraints
            next_time = curr_time + edge.time
            next_transfers = curr_transfers + edge.transfer

            # prune if the constrainst are not respected
            if next_time > max_time:
                continue

            if next_transfers > max_transfers:
                continue
            
            # update path history and push to our local backpack (local_stack)
            next_path = path + [edge]
            local_stack.append((edge.v, next_time, next_transfers, next_path))


def find_paths_parallel(
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,
    max_transfers: int,
    num_workers: int    # How many threads/processes we will have
) -> List[List[TransitEdge]]:
    manager = multiprocessing.Manager()
    shared_list = manager.list()
    lock = manager.Lock()
    solution_pool = ThreadSafeSolutionPool(
        shared_list,
        lock
    )
    
    signal_queues = {i: multiprocessing.Queue() for i in range(num_workers)}

    work_queues = {i: multiprocessing.Queue() for i in range(num_workers)}

    # tracker of active workers, at the start all of them are considered active
    active_workers = multiprocessing.Value('i', num_workers)

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
                active_workers
            )
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

    return solution_pool.get_all_solutions()
