from datetime import datetime
from typing import List
import math
import pandas as pd
from backend.models.price_point import PricePoint

class CSVCollector:
    """Loads historical CS2 market data from CSV files."""

    MIN_PLAUSIBLE_PRICE = 0.10

    @staticmethod
    def load_history(filepath: str) -> List[PricePoint]:
        df = pd.read_csv(filepath)
        history = []

        for _, row in df.iterrows():
            try:
                price = float(row["price_dollar"])
                sells = int(row["sells"])
                timestamp = datetime.fromtimestamp(row["timestamp"] / 1000)
            except (ValueError, TypeError, OverflowError):
                continue

            if not math.isfinite(price) or price < CSVCollector.MIN_PLAUSIBLE_PRICE:
                continue

            if sells < 0:
                continue

            history.append(
                PricePoint(
                    timestamp=timestamp,
                    price=price,
                    volume=sells,
                    source="steam_dataset"
                )
            )

        if not history:
            raise ValueError("No valid price history found.")

        return history