from dataclasses import dataclass

@dataclass(frozen=True)
class TransitEdge:
    u: str          # Origin node
    v: str          # Destination node
    modal: str      # Can be either 'Subway' or 'Train' or 'Bus'
    time: float     # t(e) - travel time
    cost: float     # c(e) - financial cost
    transfer: int   # tr(e) - 1 if it requires a transfer, 0 otherwise