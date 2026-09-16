from datetime import datetime
from typing import List
import math

import pandas as pd
import streamlit as st

from backend.models.price_point import PricePoint


class CSVCollector:
    """Loads historical CS2 market data from CSV files."""

    MIN_PLAUSIBLE_PRICE = 0.001

    @staticmethod
    @st.cache_data(show_spinner=False)
    def load_history(filepath: str) -> List[PricePoint]:
        df = pd.read_csv(
            filepath,
            usecols=["price", "quantity", "unix timestamp"]
        )

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["quantity"] = pd.to_numeric(
            df["quantity"],
            errors="coerce"
        )

        df["unix timestamp"] = pd.to_numeric(
            df["unix timestamp"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["price", "quantity", "unix timestamp"]
        )

        df = df[
            (df["price"] >= CSVCollector.MIN_PLAUSIBLE_PRICE)
            & (df["quantity"] >= 0)
        ]

        if df.empty:
            raise ValueError("No valid price history found.")

        history = [
            PricePoint(
                timestamp=datetime.fromtimestamp(row["unix timestamp"]),
                price=float(row["price"]),
                volume=int(row["quantity"]),
                source="steam_dataset",
            )
            for row in df.itertuples(index=False)
        ]

        return history