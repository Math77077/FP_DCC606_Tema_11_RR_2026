from typing import List, Set
from src.core.graph import Multigraph
from src.core.models import TransitEdge

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
