from typing import List
import pandas as pd
from backend.models.price_point import PricePoint
class PerformanceAnalyzer:
 # Compares performance between two assets.
    def __init__(
        self,
        history_a: List[PricePoint],
        history_b: List[PricePoint],
    ):
        if not history_a or not history_b:
            raise ValueError(
                "Both histories must contain data."
            )
        self.history_a = history_a
        self.history_b = history_b

    def _to_dataframe(
        self,
        history: List[PricePoint],
        name: str
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "timestamp": [
                    p.timestamp for p in history
                ],
                name: [
                    p.price for p in history
                ]
            }
        )

    @property
    def price_comparison(self):

        df_a = self._to_dataframe(
            self.history_a,
            "asset_a"
        )

        df_b = self._to_dataframe(
            self.history_b,
            "asset_b"
        )

        return (
            df_a.merge(
                df_b,
                on="timestamp",
                how="inner"
            )
            .sort_values("timestamp")
        )

    @property
    def normalized_returns(self):
        df = self.price_comparison.copy()

        if len(df) == 0:
            return df

        df["asset_a_normalized"] = (
            df["asset_a"]
            / df["asset_a"].iloc[0]
            * 100
        )

        df["asset_b_normalized"] = (
            df["asset_b"]
            / df["asset_b"].iloc[0]
            * 100
        )

        return df