import time
import statistics
from typing import List, Set, Tuple
from src.core.graph import Multigraph
from src.core.models import TransitEdge
from src.engines.parallel_dfs import find_alternative_paths, find_paths_parallel

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
        worker_counts: List[int]
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
        print(f"Sequential Execution Mean (T_1): {t_1:.5f} seconds")
        print(f"Total valid alternative paths discovered: {len(seq_solutions)}")

        seq_fingerprint = cls.serialize_path_list(seq_solutions)

        print("\n" + "="*70)
        print(f"{'Workers (p)':<12}{'Mean Time (Tp)':<18}{'Speedup (Sp)':<16}{'Efficiency (Ep)':<14}")
        print("="*70)

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
            if p_fingerprint != seq_fingerprint:
                print(f"ERROR: Worker configuration p={p} produced incorrect solutions!")
            
            print(f"{p:<12}{t_p:<18.5f}{speedup:<16.3f}{efficiency:<14.3%}")
        print("="*70)