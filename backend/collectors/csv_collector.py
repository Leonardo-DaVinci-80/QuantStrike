from datetime import datetime
from typing import List
import pandas as pd
from backend.models.price_point import PricePoint


class CSVCollector:
    """
    Loads historical CS2 market data from CSV files.
    """

    MIN_PLAUSIBLE_PRICE = 0.10  # anything below this is treated as bad data

    @staticmethod
    def load_history(filepath: str) -> List[PricePoint]:
        df = pd.read_csv(filepath)

        history = []
        for _, row in df.iterrows():
            price = float(row["price_dollar"])

            if price < CSVCollector.MIN_PLAUSIBLE_PRICE:
                continue  # skip implausible/placeholder prices

            point = PricePoint(
                timestamp=datetime.fromtimestamp(row["timestamp"] / 1000),
                price=price,
                volume=int(row["sells"]),
                source="steam_dataset"
            )
            history.append(point)

        return history