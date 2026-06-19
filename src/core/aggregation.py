from typing import List
from src.core.models import TransitEdge

class SolutionAggregator:
    @staticmethod
    def filter_pareto_optimal(paths: List[List[TransitEdge]]) -> List[List[TransitEdge]]:
        """
        Pareto-Dominance Post-Processing Filter.
        Extracts the non-dominated paths based on competing user metrics (pure travel time vs. line transfers).
        """

        if not paths:
            return []
        
        evaluated = []
        for p in paths:
            t = sum(e.time for e in p)
            tr = sum(e.transfer for e in p)
            evaluated.append((t, tr, p))

        optimal_paths = []
        for i, (t1, tr1, p1) in enumerate(evaluated):
            is_dominated = False
            for j, (t2, tr2, p2) in enumerate(evaluated):
                if i == j:
                    continue
                if (t2 <= t1 and tr2 <= tr1) and (t2 < t1 or tr2 < tr1):
                    is_dominated = True
                    break
            if not is_dominated:
                optimal_paths.append(p1)

        return optimal_paths