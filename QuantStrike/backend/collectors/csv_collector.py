from datetime import datetime
from typing import List
import pandas as pd
from backend.models.price_point import PricePoint

class CSVCollector:
    """
    Loads historical CS2 market data from CSV files.
    """
    @staticmethod
    def load_history(filepath: str) -> List[PricePoint]:
        df = pd.read_csv(filepath)
        history = []
        for _, row in df.iterrows():
            point = PricePoint(
                timestamp=datetime.fromtimestamp(
                    row["timestamp"] / 1000
                ),
                price=float(row["price_dollar"]),
                volume=int(row["sells"]),
                source="steam_dataset"
            )
            history.append(point)
        return history