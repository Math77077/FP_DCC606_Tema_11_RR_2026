import multiprocessing
import queue
from typing import List, Set
from src.core.graph import Multigraph
from src.core.models import TransitEdge
from src.concurrency.thread_safe_pool import ThreadSafeSolutionPool

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
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,
    max_transfers: int,
    task_queue,     # This is the shared multiprocessing.Queue()
    solution_pool: ThreadSafeSolutionPool
) -> None:
    while True:
        try:
            # We attempt to grap from the shared queue. Also,the timeout is for how long we are going to wait to grap a task, in case there isnt then throw a error (queue.Empty). We wait 0.1 seconds, no task, so error.
            task = task_queue.get(timeout=0.1) 

            # This works like a current_node = task[0], current_path = task[1], and so on
            current_node, current_path, visited_nodes, accumulated_time, accumulated_transfers = task
        except queue.Empty: # If the queue is empty, the worker can safely exit the loop
            break

        if accumulated_time > max_time:
            continue
        if accumulated_transfers > max_transfers:
            continue

        if current_node == end:
            solution_pool.add_solution(current_path)
            continue

        for edge in graph.get_neighbors(current_node):
            if edge.v not in visited_nodes:
                # This are copies of path and visited set, so separate processes dont mix into each others memory tracking
                next_path = current_path + [edge] # this is a isolated 'current_path', it doesnt touch the actual 'current_path' because the other threads are also using it. So modifying it directly means modifying the process for every thread
                next_visited = visited_nodes | {edge.v} # the same applies for this, but instead of creating a brand-new list using + [edge.v], we use '|' that works just like a Set Union, combines the current visited_nodes with a new set to create a brand-new combined set without touching the original visited_nodes

                next_time = accumulated_time + edge.time 
                next_transfers = accumulated_transfers + edge.transfer

                # Get every complete state into a tuple pack
                new_task = (edge.v, next_path, next_visited, next_time, next_transfers)

                task_queue.put(new_task) # will put this sub-task back on the queue board so any idle worker can grab it
                
                # The idea of this parallel_worker_loop is to discover a part of the path, not the whole path, but a part of it. Then, as soon it discovers this part, it just send to the TODO board tasks. When the loop reiterates again, it'll get this exactly task it just has sended to the TODO board tasks. But of course, we have to imagine this is done across multiple workers and not necessarily it'll continue the previous job


def find_paths_parallel(
    graph: Multigraph,
    start: str,
    end: str,
    max_time: float,
    max_transfers: int,
    num_workers: int    # How many threads/processes we will have
) -> List[List[TransitEdge]]:
    solution_pool = ThreadSafeSolutionPool() # This is the alternative 'all_valid_paths', but thread-safe
    task_queue = multiprocessing.Queue()     # The place where we keep the tasks. To later be stealed by other workers, so this is our initial board of TODO tasks
    task_queue.put((start, [], {start}, 0.0, 0)) # Our equivalente of dfs_worker(start, [], initial_visited, 0.0, 0) to start the system

    # This list will hold our active workers
    processes = []

    # The actual part of the code where we create the multiple workers
    for _ in range(num_workers):
        p = multiprocessing.Process(
            target=parallel_worker_loop,
            args=(graph, start, end, max_time, max_transfers, task_queue, solution_pool)
        )
        processes.append(p)
        p.start()

    for p in processes:
        p.join()  # Waits all children workers finished before finishing at the parent level process

    return solution_pool.get_all_solutions()
    

