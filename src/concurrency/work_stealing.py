import queue
from typing import List, Tuple, Optional, Dict
from src.core.models import TransitEdge

class WorkStealingManager:
    """
    It will be resposible for handling asynchronous load balancing and task splitting between isolated worker local stacks.
    """

    @staticmethod
    def split_stack(local_stack: List[Tuple[str, float, int, List[TransitEdge]]]) -> Optional[Tuple[str, float, int, List[TransitEdge]]]:
        if len(local_stack) > 1:
            stolen_frame = local_stack.pop(0)
            return stolen_frame
        return None
    
    @staticmethod
    def request_work(
        current_worker_id: int,
        num_workers: int,
        worker_queues: Dict[int, any]
    ) -> Optional[Tuple[str, float, int, List[TransitEdge]]]:
        for target_id in range(num_workers):
            if target_id == current_worker_id:
                continue

            try:
                worker_queues[target_id].put_nowait(current_worker_id)

                stolen_frame = worker_queues[current_worker_id].get(timeout=0.05)
                return stolen_frame
            except (queue.Empty, queue.Full):
                continue

        return None