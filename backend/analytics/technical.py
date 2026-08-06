import pandas as pd
from typing import List

from backend.models.price_point import PricePoint


class TechnicalAnalyzer:

    def __init__(
        self,
        history: List[PricePoint]
    ):
        if not history:
            raise ValueError("History cannot be empty.")

        self.history = sorted(
            history,
            key=lambda x: x.timestamp
        )

    @property
    def moving_average_data(self):

        df = pd.DataFrame({
            "timestamp": [p.timestamp for p in self.history],
            "price": [p.price for p in self.history]
        })

        df["MA30"] = df["price"].rolling(30).mean()
        df["MA90"] = df["price"].rolling(90).mean()

        return df