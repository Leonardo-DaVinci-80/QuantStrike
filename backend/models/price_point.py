from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class PricePoint:
    timestamp: datetime
    price: float
    volume: int | None = None
    source: str = "unknown"