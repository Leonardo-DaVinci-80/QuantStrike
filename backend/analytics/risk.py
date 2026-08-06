import pandas as pd
from typing import List

from backend.models.price_point import PricePoint


class RiskAnalyzer:
    """
    Calculates risk metrics and visualizations.
    """

    def __init__(
        self,
        history: List[PricePoint]
    ):

        if not history:
            raise ValueError(
                "History cannot be empty."
            )

        self.history = sorted(
            history,
            key=lambda x: x.timestamp
        )


    @property
    def drawdown_data(self):

        df = pd.DataFrame(
            {
                "timestamp": [
                    p.timestamp
                    for p in self.history
                ],
                "price": [
                    p.price
                    for p in self.history
                ]
            }
        )

        df["peak"] = (
            df["price"]
            .cummax()
        )

        df["drawdown"] = (
            (df["price"] - df["peak"])
            / df["peak"]
            * 100
        )

        return df