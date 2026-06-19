import os
import csv
import time
import statistics
from typing import List, Set, Tuple
from src.core.graph import Multigraph
from src.core.models import TransitEdge
from src.core.loaders import load_map_from_json
from src.engines.parallel_dfs import find_alternative_paths, find_paths_parallel
from benchmarks.generate_synthetic_data import save_synthetic_dataset

class ExperimentRunner:
    """
    Automates multi-threaded and sequential routing stress tests.
    Calculates Speedup (Sp) and Efficiency (Ep) across 13 iterations.
    """
    @staticmethod
    def serialize_path_list(paths: List[List[TransitEdge]]) -> Set[Tuple[TransitEdge, ...]]:
        serialized = set()
        for path in paths:
            path_tuple = tuple(path)
            serialized.add(path_tuple)
        return serialized
    
    @classmethod
    def run_benchmark(
        cls,
        graph: Multigraph,
        start: str,
        end: str,
        max_time: float,
        max_transfers: int,
        worker_counts: List[int],
        output_csv_path: str = "reports/metrics_scalability.csv"
    ):
        NUM_RUNS = 13
        print(f"\nRunning Sequential Baseline ({NUM_RUNS} iterations)...")
        seq_times = []
        seq_solutions: List[List[TransitEdge]] = []

        for i in range(NUM_RUNS):
            t_start = time.monotonic()
            seq_solutions = find_alternative_paths(graph, start, end, max_time, max_transfers)
            t_end = time.monotonic()
            seq_times.append(t_end - t_start)
        
        t_1 = statistics.mean(seq_times)
        total_routes = len(seq_solutions)
        print(f"Sequential Execution Mean (T_1): {t_1:.5f} seconds")
        print(f"Total valid alternative paths discovered: {len(seq_solutions)}")

        seq_fingerprint = cls.serialize_path_list(seq_solutions)

        os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
        csv_file_exists = os.path.exists(output_csv_path)

        csv_rows = []

        print("\n" + "="*70)
        print(f"{'Workers (p)':<12}{'Mean Time (Tp)':<18}{'Speedup (Sp)':<16}{'Efficiency (Ep)':<14}")
        print("="*70)

        if not csv_file_exists:
            csv_rows.append({
                "Nodes": len(graph.adjacency_list),
                "Workers": 1,
                "Mean_Time_Seconds": f"{t_1:.5f}",
                "Speedup": "1.000",
                "Efficiency": "100.00%",
                "Routes_Extracted": total_routes,
                "Status": "PASSED"
            })

        for p in worker_counts:
            p_times = []
            p_solutions = []

            for i in range(NUM_RUNS):
                t_p_start = time.monotonic()
                p_solutions = find_paths_parallel(graph, start, end, max_time, max_transfers, num_workers=p)
                t_p_end = time.monotonic()
                p_times.append(t_p_end - t_p_start)

            t_p = statistics.mean(p_times)

            speedup = t_1 / t_p
            efficiency = speedup / p

            p_fingerprint = cls.serialize_path_list(p_solutions)
            status_flag = "PASSED"
            if p_fingerprint != seq_fingerprint:
                print(f"ERROR: Worker configuration p={p} produced incorrect solutions!")
                status_flag = "FAILED"
            
            print(f"{p:<12}{t_p:<18.5f}{speedup:<16.3f}{efficiency:<14.3%}")

            csv_rows.append({
                "Nodes": len(graph.adjacency_list),
                "Workers": p,
                "Mean_Time_Seconds": f"{t_p:.5f}",
                "Speedup": f"{speedup:.3f}",
                "Efficiency": f"{efficiency:.3%}",
                "Routes_Extracted": len(p_solutions),
                "Status": status_flag
            })

        print("="*70)

        headers = ["Nodes", "Workers", "Mean_Time_Seconds", "Speedup", "Efficiency", "Routes_Extracted", "Status"]
        
        with open(output_csv_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            if not csv_file_exists:
                writer.writeheader()  
            writer.writerows(csv_rows)

if __name__ == "__main__":
    TEST_SIZE = 100
    TARGET_JSON_PATH = f"data/synthetic/network_{TEST_SIZE}_nodes.json"
    
    if not os.path.exists(TARGET_JSON_PATH):
        print(f"[TEST SETUP] Target dataset {TARGET_JSON_PATH} not found. Generating on the fly...")
        save_synthetic_dataset([TEST_SIZE])
        
    print(f"[TEST SETUP] Loading multi-modal topology from {TARGET_JSON_PATH}...")
    test_graph = load_map_from_json(TARGET_JSON_PATH)
    
    START_STATION = "Station_0"   
    END_STATION = "Station_4"       
    MAX_ALLOWABLE_TIME = 60.0       
    MAX_ALLOWABLE_TRANSFERS = 4    
    WORKER_CONFIGURATIONS = [2, 4, 8]
    
    print(f"[TEST EXECUTION] Initiating benchmarking routine from {START_STATION} to {END_STATION}...")
    print(f"Constraints: Max Time = {MAX_ALLOWABLE_TIME}s, Max Transfers = {MAX_ALLOWABLE_TRANSFERS}")
    
    ExperimentRunner.run_benchmark(
        graph=test_graph,
        start=START_STATION,
        end=END_STATION,
        max_time=MAX_ALLOWABLE_TIME,
        max_transfers=MAX_ALLOWABLE_TRANSFERS,
        worker_counts=WORKER_CONFIGURATIONS
    )