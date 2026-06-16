from typing import Dict, List
from src.core.models import TransitEdge

class Multigraph:
    def __init__(self):
        self.adjacency_list: Dict[str, List[TransitEdge]] = {}

    def add_node(self, node: str) -> None:
        """Adds a node to the graph if it doesn't exist."""
        if node not in self.adjacency_list:
            self.adjacency_list[node] = [] # Just created the fresh box, empty list for this station

    def add_edge(self, edge: TransitEdge) -> None:
        """Adds a directed edge to the graph."""
        # We need to check it the actual origin and destination nodes exists inside adjacency_list
        if edge.u not in self.adjacency_list:
            self.add_node(edge.u)
        if edge.v not in self.adjacency_list:
            self.add_node(edge.v)

        self.adjacency_list[edge.u].append(edge) # Look for the box name and adds the connection from origin to destination
        
    def get_neighbors(self, node: str) -> List[TransitEdge]:
        """Returns all neighbors edges from a given node."""
        # We also need to check if the box exists, if case of not existing, then just return the usual empty list
        if node not in self.adjacency_list:
            return []
        else:
            return self.adjacency_list[node] # Every moment we are asked: 'Which routes como from Station_X?', we just return the box, because inside it there are the actual connections. So the neighbors
        # Another cleaner way of doing it, it's self.adjacency_list.get(node, [])
        # It searchs the node, if exists, then return the box's inside. Otherwise, return the default []