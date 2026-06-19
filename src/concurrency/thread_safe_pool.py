from multiprocessing.managers import SyncManager
from typing import List, Tuple
from src.core.models import TransitEdge

class ThreadSafeSolutionPool:
    """
    Thread-safe repository that collects discovered target paths using a shared multi-processing proxy list.
    """
    def __init__(self, manager: SyncManager):
        self._shared_list =  manager.list()
        self._lock = manager.Lock()

    def add_solution(self, path: List[TransitEdge]) -> None:
        """Safely appends a valid path clone to the global shared list."""
        with self._lock:
            self._shared_list.append(list(path))

    def get_all_solutions(self) -> List[List[TransitEdge]]:
        """Returns a standard snapshot list copy of all collected solutions."""
        with self._lock:
            return list(self._shared_list)
        
class ThreadSafeDominanceFrontier:
    """
    Extends data synchronization across isolated CPU processes.
    Tracks globally discovered optimal bounds using a Pareto-front archive.
    """
    def __init__(self, manager: SyncManager):
        self._shared_dict = manager.dict()
        self._lock = manager.Lock()

    def should_prune(self, node: str, current_time: float, current_transfers: int) -> bool:
        """
        Thread-safe verification to check if a better or equal path has already been registered.
        """
        if node not in self._shared_dict:
            return False
            
        for best_time, best_transfers in self._shared_dict[node]:
            if current_time >= best_time and current_transfers >= best_transfers:
                return True
        return False
            
    def update_frontier(self, node: str, current_time: float, current_transfers: int) -> bool:
        """
        Attempts to update the dominance bounds for a node.
        """
        with self._lock:
            current_front = self._shared_dict.get(node, [])
            
            for best_time, best_transfers in current_front:
                if current_time >= best_time and current_transfers >= best_transfers:
                    return False
            
            new_front = [(t, tr) for (t, tr) in current_front if not (current_time <= t and current_transfers <= tr)]
            new_front.append((current_time, current_transfers))
            
            self._shared_dict[node] = new_front
            return True