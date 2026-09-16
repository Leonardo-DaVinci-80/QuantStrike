from pathlib import Path
import pandas as pd


class DailyMarketDataBuilder:
    """
    Builds derived daily market data from raw history CSV files.

    Raw/native observations remain untouched.
    Daily data is stored separately for market-wide analytics.
    """

    def __init__(self, repository):
        self.repository = repository

    @staticmethod
    def build_daily_data_from_df(df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert one raw history DataFrame into daily median prices.

        Returns columns:
            date
            price
            observation_count
        """

        if df.empty:
            return pd.DataFrame(
                columns=["date", "price", "observation_count"]
            )

        df = df.copy()

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["unix timestamp"] = pd.to_numeric(
            df["unix timestamp"],
            errors="coerce"
        )

        df = df.dropna(
            subset=["price", "unix timestamp"]
        )

        df = df[
            df["price"] >= 0.001
        ]

        if df.empty:
            return pd.DataFrame(
                columns=["date", "price", "observation_count"]
            )

        df["timestamp"] = pd.to_datetime(
            df["unix timestamp"],
            unit="s",
            errors="coerce"
        )

        df = df.dropna(
            subset=["timestamp"]
        )

        if df.empty:
            return pd.DataFrame(
                columns=["date", "price", "observation_count"]
            )

        df = df.set_index("timestamp").sort_index()

        daily = df["price"].resample("D").agg(
            price="median",
            observation_count="count"
        )

        daily = daily.reset_index()
        daily = daily.rename(
            columns={"timestamp": "date"}
        )

        return daily

    def build_daily_dataset(
        self,
        max_assets=None,
        min_observations=30,
    ) -> pd.DataFrame:
        """
        Build the complete long-format daily dataset.

        Columns:
            date
            asset_id
            name
            price
            observation_count
        """

        records = []

        index = self.repository.index

        if max_assets is not None:
            index = index.head(max_assets)

        total = len(index)

        for i, (_, row) in enumerate(index.iterrows(), 1):

            filepath = (
                Path(self.repository.items_directory)
                / row["file_name"]
            )

            if not filepath.exists():
                continue

            try:
                df = pd.read_csv(
                    filepath,
                    usecols=["price", "unix timestamp"]
                )
            except Exception:
                continue

            if len(df) < min_observations:
                continue

            daily = self.build_daily_data_from_df(df)

            if daily.empty:
                continue

            daily["asset_id"] = row["URL encoded name"]
            daily["name"] = row["name"]

            records.append(daily)

            if i % 500 == 0:
                print(
                    f"Processed {i:,} / {total:,}"
                )

        if not records:
            return pd.DataFrame(
                columns=[
                    "date",
                    "asset_id",
                    "name",
                    "price",
                    "observation_count",
                ]
            )

        result = pd.concat(
            records,
            ignore_index=True
        )

        result = result[
            [
                "date",
                "asset_id",
                "name",
                "price",
                "observation_count",
            ]
        ]

        result = result.sort_values(
            ["date", "asset_id"]
        ).reset_index(drop=True)

        return result