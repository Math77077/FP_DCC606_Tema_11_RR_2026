import json
from typing import Dict
from src.core.graph import Multigraph
from src.core.models import TransitEdge

def load_map_from_json(file_path: str) -> Multigraph:
    """Loads JSON data and populates a Multigraph instance."""
    graph = Multigraph()

    with open(file_path, "r") as file:
        data = json.load(file)   # Loading the JSON file into a list of dicts
        # data is a dict; data["connections"] is the actual list of dicts

    for conn in data["connections"]:
        extracted_data = TransitEdge(
            u=conn["origin"], 
            v=conn["destination"], 
            modal=conn["modal"], 
            time=conn["time"], 
            cost=conn["cost"], 
            transfer=conn["transfer"]
        ) # Creating the TransitEdge object for the individual data
        graph.add_edge(extracted_data) # Adding the individual data into the graph as a edge
        
    return graph