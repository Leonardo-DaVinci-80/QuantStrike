from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PricePoint:
    """
    Represents a single historical market price.
    """

    timestamp: datetime
    price: float
    volume: int | None = None
    source: str = "openskin"