import os
import json
import random

def generate_metropolitan_network(num_nodes: int, hubs_count: int) -> dict:
    network = {
        "metadata": {"nodes": num_nodes, "hubs": hubs_count},
        "connections": []
    }

    nodes = [f"Station_{i}" for i in range(num_nodes)]
    hubs = nodes[:hubs_count]
    local_nodes = nodes[hubs_count:]

    for i in range(len(hubs)):
        for j in range(i + 1, len(hubs)):
            if random.random() < 0.4:
                u, v = hubs[i], hubs[j]
                travel_time = random.uniform(5.0, 15.0)
                financial_cost = random.uniform(4.0, 6.0)

                for origin, destination in [(u, v), (v,u)]:
                    network["connections"].append({
                        "origin": origin,
                        "destination": destination,
                        "modal": random.choice(["Subway", "Train"]),
                        "time": round(travel_time, 2),
                        "cost": round(financial_cost, 2),
                        "transfer": 1
                    })
    
    for node in local_nodes:
        target_hub = random.choice(hubs)
        travel_time = random.uniform(2.0, 8.0)
        financial_cost = random.uniform(1.5, 3.0)

        for origin, destination in [(node, target_hub), (target_hub, node)]:
            network["connections"].append({
                "origin": origin,       
                "destination": destination,
                "modal": "Bus",
                "time": round(travel_time, 2),
                "cost": round(financial_cost, 2),
                "transfer": 0
            })
    
    return network

def save_synthetic_dataset(node_counts: list):
    os.makedirs("data/synthetic", exist_ok=True)

    for size in node_counts:
        hubs_size = max(2, int(size * 0.05))
        print(f"Generating synthetic topology: {size} nodes, {hubs_size} hubs...")

        data = generate_metropolitan_network(size, hubs_size)

        output_path = f"data/synthetic/network_{size}_nodes.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Successfully saved to {output_path}")

if __name__ == "__main__":
    save_synthetic_dataset([100])