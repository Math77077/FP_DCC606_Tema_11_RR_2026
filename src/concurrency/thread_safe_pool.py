from multiprocessing import Manager
from typing import List
from src.core.models import TransitEdge

class ThreadSafeSolutionPool:
    def __init__(self, shared_list, lock):
        self._shared_list = shared_list
        self._lock = lock

    def add_solution(self, path: List[TransitEdge]) -> None:
        """Safely appends a valid path to the global shared list."""
        with self._lock: # This 'with' do the .acquire() and .release() of lock automatically
            self._shared_list.append(list(path)) # We append the path, just like we did in parallel_dfs.py in the dfs_worker when current_node == end

    def get_all_solutions(self) -> List[List[TransitEdge]]:
        """Returns a snapshot copy of all collected solutions."""
        # It'll convert the shared manager list back into a standard Python list
        with self._lock: 
            return list(self._shared_list)