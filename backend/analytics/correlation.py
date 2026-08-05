from typing import List
import pandas as pd

from backend.models.price_point import PricePoint


class CorrelationAnalyzer:
    """
    Calculates the relationship between two asset price histories.
    Uses return correlation rather than price correlation.
    """

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


    def _history_to_dataframe(
        self,
        history: List[PricePoint],
        column_name: str,
    ) -> pd.DataFrame:

        return pd.DataFrame(
            {
                "timestamp": [
                    point.timestamp
                    for point in history
                ],
                column_name: [
                    point.price
                    for point in history
                ],
            }
        )


    @property
    def aligned_prices(self) -> pd.DataFrame:
        """
        Returns only dates where both assets have prices.
        """

        asset_a = self._history_to_dataframe(
            self.history_a,
            "asset_a"
        )

        asset_b = self._history_to_dataframe(
            self.history_b,
            "asset_b"
        )

        return (
            asset_a
            .merge(
                asset_b,
                on="timestamp",
                how="inner"
            )
            .sort_values("timestamp")
        )


    @property
    def returns(self) -> pd.DataFrame:
        """
        Calculates daily percentage returns.
        """

        df = self.aligned_prices.copy()

        df["return_a"] = (
            df["asset_a"]
            .pct_change()
        )

        df["return_b"] = (
            df["asset_b"]
            .pct_change()
        )

        return df.dropna()


    @property
    def correlation(self) -> float:
        """
        Pearson correlation coefficient
        between asset returns.
        """

        df = self.returns

        return round(
            df["return_a"]
            .corr(df["return_b"]),
            3
        )


    @property
    def correlation_strength(self) -> str:

        value = self.correlation

        if value >= 0.9:
            return "Very Strong Positive"

        elif value >= 0.7:
            return "Strong Positive"

        elif value >= 0.4:
            return "Moderate Positive"

        elif value >= 0.2:
            return "Weak Positive"

        elif value > -0.2:
            return "Little to No Correlation"

        elif value > -0.4:
            return "Weak Negative"

        elif value > -0.7:
            return "Moderate Negative"

        elif value > -0.9:
            return "Strong Negative"

        return "Very Strong Negative"

    @property
    def observation_count(self) -> int:
        return len(self.returns)

    @property
    def return_pairs(self):
        return self.returns