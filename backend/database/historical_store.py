from datetime import datetime
from pathlib import Path
from typing import List

import pandas as pd
import streamlit as st

from backend.models.price_point import PricePoint


class HistoricalStore:
    """
    Reads historical price data from the processed Parquet dataset.

    Only the requested skin's rows are loaded into memory rather than
    loading the entire historical dataset.
    """

    def __init__(
        self,
        historical_file: str,
        metadata_file: str | None = None,
    ):
        self.historical_file = Path(historical_file)
        self.metadata_file = (
            Path(metadata_file) if metadata_file else None
        )

        if not self.historical_file.exists():
            raise FileNotFoundError(
                f"Historical data file not found: {self.historical_file}"
            )

        if self.metadata_file and not self.metadata_file.exists():
            raise FileNotFoundError(
                f"Metadata file not found: {self.metadata_file}"
            )

    @st.cache_data(
        show_spinner=False,
        max_entries=100,
        ttl=60 * 60 * 24,
    )
    def _load_skin_dataframe(
        _self,
        skin_id: str,
    ) -> pd.DataFrame:
        """
        Load only one skin from the Parquet dataset.

        PyArrow's Parquet filtering allows the reader to avoid loading
        unrelated rows wherever row-group statistics permit pruning.
        """

        df = pd.read_parquet(
            _self.historical_file,
            engine="pyarrow",
            columns=[
                "skin_id",
                "timestamp",
                "price",
                "volume",
            ],
            filters=[
                ("skin_id", "==", skin_id),
            ],
        )

        if df.empty:
            raise ValueError(
                f"No historical data found for skin_id: {skin_id}"
            )

        return df.sort_values("timestamp").reset_index(drop=True)

    def load_history(self, skin_id: str) -> List[PricePoint]:
        """
        Load historical observations for a single skin.
        """

        df = self._load_skin_dataframe(skin_id)

        history = [
            PricePoint(
                timestamp=datetime.fromtimestamp(int(row.timestamp)),
                price=float(row.price),
                volume=(
                    int(row.volume)
                    if pd.notna(row.volume)
                    else None
                ),
                source="steam_dataset",
            )
            for row in df.itertuples(index=False)
        ]

        return history

    def load_history_dataframe(self, skin_id: str) -> pd.DataFrame:
        """
        Return the selected skin's historical data as a DataFrame.

        Useful for analytics that work directly with pandas.
        """

        return self._load_skin_dataframe(skin_id).copy()