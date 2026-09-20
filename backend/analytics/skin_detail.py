from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb
import pandas as pd


class SkinDetailAnalyzer:
    """
    Skin-specific analytics for QuantStrike.

    Historical schema:
        skin_id   : encoded item filename / unique asset identifier
        timestamp : Unix timestamp in seconds
        price     : observed price
        volume    : observed sale volume

    The historical dataset is intentionally queried with DuckDB
    so the complete 105M+ row dataset is never loaded into pandas.
    """

    def __init__(
        self,
        historical_file: str | Path,
        cache_file: str | Path | None = None,
    ):
        self.historical_file = Path(historical_file)

        if not self.historical_file.exists():
            raise FileNotFoundError(
                f"Historical dataset not found:\n"
                f"{self.historical_file}"
            )

        if cache_file is None:
            cache_file = (
                self.historical_file.parent.parent
                / "cache"
                / "skin_daily.parquet"
            )

        self.cache_file = Path(cache_file)

        self.cache_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ==========================================================
    # CONNECTION
    # ==========================================================

    def _connect(self):
        return duckdb.connect()

    # ==========================================================
    # HISTORY
    # ==========================================================

    def get_history(
        self,
        skin_id: Optional[str] = None,
        name: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Return every historical observation for one skin.

        skin_id is the primary identifier.

        `name` is retained as a fallback for compatibility with
        the frontend, but the historical dataset itself only
        contains skin_id.
        """

        if skin_id is None:
            raise ValueError(
                "skin_id is required for the historical dataset."
            )

        query = """
            SELECT
                skin_id,
                timestamp,
                price,
                volume
            FROM read_parquet(?)
            WHERE skin_id = ?
            ORDER BY timestamp
        """

        with self._connect() as con:
            df = con.execute(
                query,
                [
                    str(self.historical_file),
                    skin_id,
                ],
            ).df()

        if df.empty:
            return df

        # Historical timestamps are Unix seconds.
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="s",
            errors="coerce",
            utc=True,
        ).dt.tz_convert(None)

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce",
        )

        df["volume"] = pd.to_numeric(
            df["volume"],
            errors="coerce",
        ).fillna(0)

        df = (
            df.dropna(
                subset=[
                    "timestamp",
                    "price",
                ]
            )
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        return df

    # ==========================================================
    # DAILY HISTORY
    # ==========================================================

    def get_daily_history(
        self,
        skin_id: Optional[str] = None,
        name: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Produce one record per calendar day for one skin.

        Fields:
            date
            low
            median
            average
            high
            close
            observations
            volume
        """

        if skin_id is None:
            raise ValueError(
                "skin_id is required for the historical dataset."
            )

        query = """
            SELECT
                CAST(
                    DATE_TRUNC(
                        'day',
                        TO_TIMESTAMP(timestamp)
                    ) AS DATE
                ) AS date,

                MIN(price) AS low,
                MEDIAN(price) AS median,
                AVG(price) AS average,
                MAX(price) AS high,

                ARG_MAX(
                    price,
                    timestamp
                ) AS close,

                COUNT(*) AS observations,
                SUM(volume) AS volume

            FROM read_parquet(?)

            WHERE
                skin_id = ?
                AND price IS NOT NULL
                AND timestamp IS NOT NULL

            GROUP BY 1

            ORDER BY date
        """

        with self._connect() as con:
            daily = con.execute(
                query,
                [
                    str(self.historical_file),
                    skin_id,
                ],
            ).df()

        if daily.empty:
            return daily

        daily["date"] = pd.to_datetime(
            daily["date"]
        )

        daily["observations"] = (
            daily["observations"]
            .astype(int)
        )

        daily["volume"] = pd.to_numeric(
            daily["volume"],
            errors="coerce",
        ).fillna(0)

        return daily

    # ==========================================================
    # DATE EXPLORER
    # ==========================================================

    def get_date_observations(
        self,
        date,
        skin_id: Optional[str] = None,
        name: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Return every historical observation for a specific
        calendar date.
        """

        if skin_id is None:
            raise ValueError(
                "skin_id is required for the historical dataset."
            )

        target = pd.Timestamp(date).strftime(
            "%Y-%m-%d"
        )

        query = """
            SELECT
                skin_id,
                timestamp,
                price,
                volume
            FROM read_parquet(?)

            WHERE
                skin_id = ?
                AND CAST(
                    TO_TIMESTAMP(timestamp)
                    AS DATE
                ) = CAST(? AS DATE)

            ORDER BY timestamp
        """

        with self._connect() as con:
            df = con.execute(
                query,
                [
                    str(self.historical_file),
                    skin_id,
                    target,
                ],
            ).df()

        if df.empty:
            return df

        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            unit="s",
            errors="coerce",
            utc=True,
        ).dt.tz_convert(None)

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce",
        )

        df["volume"] = pd.to_numeric(
            df["volume"],
            errors="coerce",
        ).fillna(0)

        return (
            df.dropna(
                subset=[
                    "timestamp",
                    "price",
                ]
            )
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

    # ==========================================================
    # DATE SUMMARY
    # ==========================================================

    def get_date_summary(
        self,
        date,
        skin_id: Optional[str] = None,
        name: Optional[str] = None,
        condition: Optional[str] = None,
    ) -> dict:
        """
        Calculate summary statistics for a single calendar date.
        """

        if skin_id is None:
            raise ValueError(
                "skin_id is required for the historical dataset."
            )

        target = pd.Timestamp(date).strftime(
            "%Y-%m-%d"
        )

        query = """
            SELECT
                MIN(price) AS low,
                MEDIAN(price) AS median,
                AVG(price) AS average,
                MAX(price) AS high,
                COUNT(*) AS observations,
                SUM(volume) AS volume

            FROM read_parquet(?)

            WHERE
                skin_id = ?
                AND CAST(
                    TO_TIMESTAMP(timestamp)
                    AS DATE
                ) = CAST(? AS DATE)
        """

        with self._connect() as con:
            row = con.execute(
                query,
                [
                    str(self.historical_file),
                    skin_id,
                    target,
                ],
            ).fetchone()

        if row is None or row[4] == 0:
            return {
                "observations": 0,
                "low": None,
                "median": None,
                "average": None,
                "high": None,
                "volume": 0,
            }

        return {
            "observations": int(row[4]),
            "low": float(row[0]),
            "median": float(row[1]),
            "average": float(row[2]),
            "high": float(row[3]),
            "volume": float(row[5] or 0),
        }

    # ==========================================================
    # PERFORMANCE
    # ==========================================================

    @staticmethod
    def _return(
        current,
        previous,
    ):
        if previous is None:
            return None

        if previous == 0:
            return None

        return (
            current / previous - 1
        ) * 100

    def performance(
        self,
        daily: pd.DataFrame,
    ) -> dict:
        """
        Calculate price performance over standard periods.
        """

        if daily.empty:
            return {}

        daily = (
            daily
            .sort_values("date")
            .reset_index(drop=True)
        )

        latest = daily.iloc[-1]

        current = float(
            latest["close"]
        )

        latest_date = pd.Timestamp(
            latest["date"]
        )

        def price_at_or_before(days):
            target = (
                latest_date
                - pd.Timedelta(
                    days=days
                )
            )

            eligible = daily[
                daily["date"] <= target
            ]

            if eligible.empty:
                return None

            return float(
                eligible.iloc[-1]["close"]
            )

        p7 = price_at_or_before(7)
        p30 = price_at_or_before(30)
        p90 = price_at_or_before(90)
        p365 = price_at_or_before(365)

        first = float(
            daily.iloc[0]["close"]
        )

        return {
            "current": current,

            "7d": self._return(
                current,
                p7,
            ),

            "30d": self._return(
                current,
                p30,
            ),

            "90d": self._return(
                current,
                p90,
            ),

            "1y": self._return(
                current,
                p365,
            ),

            "all_time": self._return(
                current,
                first,
            ),
        }

    # ==========================================================
    # STATISTICS
    # ==========================================================

    def statistics(
        self,
        history: pd.DataFrame,
        daily: pd.DataFrame,
    ) -> dict:
        """
        Calculate historical statistics.
        """

        if history.empty:
            return {}

        prices = history["price"]

        ath_index = prices.idxmax()
        atl_index = prices.idxmin()

        ath_row = history.loc[
            ath_index
        ]

        atl_row = history.loc[
            atl_index
        ]

        if len(history) >= 2:

            returns = (
                history["price"]
                .pct_change()
                .replace(
                    [
                        float("inf"),
                        float("-inf"),
                    ],
                    pd.NA,
                )
                .dropna()
            )

            volatility = (
                float(
                    returns.std() * 100
                )
                if not returns.empty
                else None
            )

        else:
            volatility = None

        total_volume = float(
            history["volume"].sum()
        )

        return {
            "ath": float(
                prices.max()
            ),

            "ath_date": ath_row[
                "timestamp"
            ],

            "atl": float(
                prices.min()
            ),

            "atl_date": atl_row[
                "timestamp"
            ],

            "median": float(
                prices.median()
            ),

            "average": float(
                prices.mean()
            ),

            "volatility": volatility,

            "observations": int(
                len(history)
            ),

            "days": int(
                len(daily)
            ),

            "volume": total_volume,
        }

    # ==========================================================
    # ANOMALIES
    # ==========================================================

    def detect_anomalies(
        self,
        history: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        Flag isolated extreme price observations.

        These are NOT declared fake or fraudulent.

        They are observations that exhibit:
            - a very large drop
            - followed by a substantial recovery
            - and, where available, volume <= 1
        """

        if history.empty:
            return pd.DataFrame()

        df = (
            history
            .copy()
            .sort_values("timestamp")
            .reset_index(drop=True)
        )

        df["previous_price"] = (
            df["price"].shift(1)
        )

        df["next_price"] = (
            df["price"].shift(-1)
        )

        df["crash_ratio"] = (
            df["price"]
            / df["previous_price"]
        )

        df["recovery_ratio"] = (
            df["next_price"]
            / df["price"]
        )

        isolated = (
            (df["crash_ratio"] < 0.25)
            &
            (df["recovery_ratio"] > 2.0)
        )

        if "volume" in df.columns:
            isolated = (
                isolated
                &
                (df["volume"] <= 1)
            )

        anomalies = df.loc[
            isolated
        ].copy()

        if anomalies.empty:
            return anomalies

        anomalies["classification"] = (
            "isolated_single_sale_anomaly"
        )

        anomalies["crash_pct"] = (
            1
            - anomalies["crash_ratio"]
        ) * 100

        anomalies["recovery_pct"] = (
            anomalies["recovery_ratio"]
            - 1
        ) * 100

        return anomalies

    # ==========================================================
    # CACHE BUILDER
    # ==========================================================

    def build_daily_cache(
        self,
        force: bool = False,
    ):
        """
        Build one daily aggregate per skin.

        This performs a one-time full scan of the historical
        dataset using DuckDB.
        """

        if (
            self.cache_file.exists()
            and not force
        ):
            return self.cache_file

        query = """
            COPY (

                SELECT
                    skin_id,

                    CAST(
                        DATE_TRUNC(
                            'day',
                            TO_TIMESTAMP(timestamp)
                        ) AS DATE
                    ) AS date,

                    MIN(price) AS low,
                    MEDIAN(price) AS median,
                    AVG(price) AS average,
                    MAX(price) AS high,

                    ARG_MAX(
                        price,
                        timestamp
                    ) AS close,

                    COUNT(*) AS observations,

                    SUM(volume) AS volume

                FROM read_parquet(?)

                WHERE
                    price IS NOT NULL
                    AND timestamp IS NOT NULL

                GROUP BY
                    skin_id,
                    DATE_TRUNC(
                        'day',
                        TO_TIMESTAMP(timestamp)
                    )

                ORDER BY
                    skin_id,
                    date

            )

            TO ?

            (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
        """

        with self._connect() as con:
            con.execute(
                query,
                [
                    str(self.historical_file),
                    str(self.cache_file),
                ],
            )

        return self.cache_file

    # ==========================================================
    # RELATED ITEMS
    # ==========================================================

    def related_items(
        self,
        index: pd.DataFrame,
        selected_name: str,
        limit: int = 10,
    ) -> pd.DataFrame:
        """
        Find related items using the existing 22,495-item
        metadata index.
        """

        if index.empty:
            return index

        required = {
            "name",
            "weapon",
        }

        if not required.issubset(
            index.columns
        ):
            return pd.DataFrame()

        selected_rows = index[
            index["name"] == selected_name
        ]

        if selected_rows.empty:
            return pd.DataFrame()

        selected = selected_rows.iloc[0]

        weapon = str(
            selected["weapon"]
        )

        result = index[
            (
                index["weapon"]
                .astype(str)
                == weapon
            )
            &
            (
                index["name"]
                != selected_name
            )
        ].copy()

        return result.head(limit)