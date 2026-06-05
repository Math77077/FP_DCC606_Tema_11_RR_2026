from multiprocessing import Manager
from typing import List
from src.core.models import TransitEdge

class ThreadSafeSolutionPool:
    def __init__(self):
        self._manager = Manager() # The manager will open the possibility of creating data structures that can be shared across completely separate CPU processes safely

        self._shared_list = self._manager.list() # This is our list where all valid paths will accumulate

        self._lock = self._manager.Lock() # This is the lock which enables just one worker writing at a time.
        # So by doing that, we avoid overlapping information, overwritting or crashing the program

    def add_solution(self, path: List[TransitEdge]) -> None:
        """Safely appends a valid path to the global shared list."""
        with self._lock: # This 'with' do the .acquire() and .release() of lock automatically
            self._shared_list.append(list(path)) # We append the path, just like we did in parallel_dfs.py in the dfs_worker when current_node == end

    def get_all_solutions(self) -> List[List[TransitEdge]]:
        """Returns a snapshot copy of all collected solutions."""
        # It'll convert the shared manager list back into a standard Python list
        with self._lock: 
            return list(self._shared_list)