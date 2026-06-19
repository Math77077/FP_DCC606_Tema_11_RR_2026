import queue
from typing import List, Tuple, Optional, Dict
from src.core.models import TransitEdge

class WorkStealingManager:
    """
    It will be resposible for handling asynchronous load balancing and task splitting between isolated worker local stacks.
    """

    @staticmethod
    def split_stack(local_stack: List[Tuple[str, float, int, List[TransitEdge]]]) -> Optional[Tuple[str, float, int, List[TransitEdge]]]:
        """
        Extracts a coarse-grained task chunck from the bottom of the target's stack to minimize IPC overhead.
        """
        if len(local_stack) <= 1:
            return None
        
        try:
            stolen_item = local_stack.pop(0)
            node, curr_time, curr_transfers, path_history = stolen_item
            return (node, curr_time, curr_transfers, list(path_history))
        except IndexError:
            return None
    
    @staticmethod
    def request_work(
        current_worker_id: int,
        num_workers: int,
        signal_queues: Dict[int, any], # dedicated to passing thief IDs
        work_queues: Dict[int, any]    # dedicated to passing task frames
    ) -> Optional[Tuple[str, float, int, List[TransitEdge]]]:
        for target_id in range(num_workers):
            if target_id == current_worker_id: #avoids a worker stealing from itself
                continue

            try:
                signal_queues[target_id].put_nowait(current_worker_id)
                stolen_frame = work_queues[current_worker_id].get(timeout=0.02)

                if stolen_frame:
                    return stolen_frame

            except (queue.Empty, queue.Full): #if the target's signal queue is full, or our work queue stays empty, move on to check the next available worker
                continue

        return None