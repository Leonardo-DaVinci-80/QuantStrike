from typing import Dict, List

import pandas as pd

from backend.collectors.csv_collector import CSVCollector
from backend.models.price_point import PricePoint
from backend.repositories.skin_repository import SkinRepository


class MarketOverviewAnalyzer:
    """
    Market-wide analytics for QuantStrike.

    Builds a daily price matrix across the tracked CS2 skin universe.
    """

    def __init__(
        self,
        repository: SkinRepository,
        min_observations: int = 30,
    ):
        self.repository = repository
        self.min_observations = min_observations

        self._histories: Dict[str, List[PricePoint]] | None = None
        self._daily_prices: pd.DataFrame | None = None

    # ---------------------------------------------------------
    # DATA LOADING
    # ---------------------------------------------------------

    def load_histories(self) -> Dict[str, List[PricePoint]]:
        """
        Load valid historical price data for all tracked skins.

        Histories are cached in memory so CSV files are only
        read once per analyzer instance.
        """

        if self._histories is not None:
            return self._histories

        histories = {}

        for _, row in self.repository.index.iterrows():

            name = row["name"]

            filepath = (
                f"{self.repository.items_directory}/"
                f"{row['file_name']}"
            )

            try:
                history = CSVCollector.load_history(filepath)

            except (FileNotFoundError, ValueError):
                continue

            if len(history) < self.min_observations:
                continue

            histories[name] = history

        self._histories = histories

        return histories

    # ---------------------------------------------------------
    # DAILY PRICE MATRIX
    # ---------------------------------------------------------

    def build_daily_price_matrix(self) -> pd.DataFrame:
        """
        Convert all skin histories into a daily price matrix.

        Each column represents one skin.
        Each row represents one calendar day.

        The daily price is the final observed price for that day.
        """

        if self._daily_prices is not None:
            return self._daily_prices

        histories = self.load_histories()

        series = []

        for name, history in histories.items():

            df = pd.DataFrame(
                {
                    "timestamp": [
                        point.timestamp
                        for point in history
                    ],
                    "price": [
                        point.price
                        for point in history
                    ],
                }
            )

            df["timestamp"] = pd.to_datetime(
                df["timestamp"]
            )

            df = df.sort_values("timestamp")

            daily = (
                df.set_index("timestamp")["price"]
                .resample("D")
                .last()
                .dropna()
            )

            daily.name = name

            series.append(daily)

        if not series:
            raise ValueError(
                "No valid price histories available."
            )

        matrix = pd.concat(
            series,
            axis=1
        ).sort_index()

        self._daily_prices = matrix

        return matrix

    # ---------------------------------------------------------
    # DAILY RETURNS
    # ---------------------------------------------------------

    def build_daily_returns(self) -> pd.DataFrame:
        """
        Calculate daily returns for every asset.

        Returns are only calculated when an asset has valid prices
        on consecutive calendar days.
        """

        prices = self.build_daily_price_matrix()

        returns = pd.DataFrame(
            index=prices.index,
            columns=prices.columns,
            dtype=float
        )

        for column in prices.columns:

            series = prices[column].dropna()

            if len(series) < 2:
                continue

            previous = series.shift(1)

            # Only accept genuinely consecutive observations.
            consecutive = (
                series.index.to_series().diff().dt.days == 1
            )

            asset_returns = (
                series / previous - 1
            )

            asset_returns = asset_returns.where(
                consecutive
            )

            # Remove pathological historical observations.
            asset_returns = asset_returns.clip(
                lower=-0.50,
                upper=0.50
            )

            returns.loc[
                asset_returns.index,
                column
            ] = asset_returns

        return returns

    # ---------------------------------------------------------
    # MARKET BREADTH
    # ---------------------------------------------------------

    def market_breadth(self) -> pd.DataFrame:
        """
        Calculate advancing, declining and unchanged assets
        for each day.
        """

        returns = self.build_daily_returns()

        advancing = (returns > 0).sum(axis=1)
        declining = (returns < 0).sum(axis=1)
        unchanged = (returns == 0).sum(axis=1)

        return pd.DataFrame(
            {
                "advancing": advancing,
                "declining": declining,
                "unchanged": unchanged,
            }
        )

    # ---------------------------------------------------------
    # QSI
    # ---------------------------------------------------------

# ---------------------------------------------------------
# QSI
# ---------------------------------------------------------

    def calculate_qsi(self) -> pd.Series:
        """
        Calculate the QuantStrike Index (QSI).

        Method:
        - Equal-weighted market return
        - Only include dates with >=50% market coverage
        - Cap individual asset returns at +/-50%
        - QSI starts at 1,000
        """

        returns = self.build_daily_returns()

        # -----------------------------------------------------
        # Coverage
        # -----------------------------------------------------

        coverage = returns.notna().sum(axis=1)

        total_assets = len(self.load_histories())

        if total_assets == 0:
            raise ValueError("No assets available for QSI.")

        coverage_ratio = coverage / total_assets

        # Require at least 50% of the tracked market to have
        # valid returns on a given day.
        valid_dates = coverage_ratio >= 0.50

        returns = returns.loc[valid_dates]

        if returns.empty:
            raise ValueError(
                "No dates meet the minimum QSI coverage requirement."
            )

        # -----------------------------------------------------
        # Remove extreme / corrupted individual returns
        # -----------------------------------------------------

        returns = returns.clip(
            lower=-0.50,
            upper=0.50
        )

        # -----------------------------------------------------
        # Equal-weighted market return
        # -----------------------------------------------------

        market_returns = returns.mean(
            axis=1,
            skipna=True
        )

        market_returns = market_returns.dropna()

        if market_returns.empty:
            raise ValueError(
                "Unable to calculate QSI."
            )

        # -----------------------------------------------------
        # Calculate index
        # -----------------------------------------------------

        qsi = (1 + market_returns).cumprod() * 1000

        qsi.name = "QSI"

        return qsi

    # ---------------------------------------------------------
    # MARKET RETURNS
    # ---------------------------------------------------------

    def market_returns(self) -> pd.Series:
        """
        Return the robust daily market return.

        Uses the median return across tracked assets
        to reduce the influence of extreme historical outliers.
        """

        returns = self.build_daily_returns()

        return returns.median(
            axis=1,
            skipna=True
        )
    def latest_market_snapshot(self) -> dict:
        """
        Return the latest available market-wide statistics.
        """

        returns = self.build_daily_returns()

        latest = returns.dropna(how="all").iloc[-1]

        advancing = int((latest > 0).sum())
        declining = int((latest < 0).sum())
        unchanged = int((latest == 0).sum())

        return {
            "market_return": latest.mean(),
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "volatility": latest.std(),
        }


    def top_movers(self, n: int = 10):

        prices = self.build_daily_price_matrix()
        returns = self.build_daily_returns()

        latest_prices = prices.dropna(how="all").iloc[-1]
        latest_returns = returns.dropna(how="all").iloc[-1]

        movers = pd.DataFrame({
            "price": latest_prices,
            "return": latest_returns,
        }).dropna()

        gainers = (
            movers
            .sort_values("return", ascending=False)
            .head(n)
        )

        losers = (
            movers
            .sort_values("return", ascending=True)
            .head(n)
        )

        return gainers, losers

        # ---------------------------------------------------------
    # CURRENT MARKET SNAPSHOT
    # ---------------------------------------------------------

    def latest_market_snapshot(self) -> dict:
        """
        Return the latest available market-wide statistics.
        """

        returns = self.build_daily_returns()

        latest = returns.dropna(how="all").iloc[-1]

        advancing = int((latest > 0).sum())
        declining = int((latest < 0).sum())
        unchanged = int((latest == 0).sum())

        market_return = latest.mean()

        volatility = latest.std()

        return {
            "market_return": market_return,
            "advancing": advancing,
            "declining": declining,
            "unchanged": unchanged,
            "volatility": volatility,
        }

    # ---------------------------------------------------------
    # TOP GAINERS / LOSERS
    # ---------------------------------------------------------

    def top_movers(self, n: int = 10):
        """
        Return the strongest gainers and losers from the
        latest available market session.
        """

        prices = self.build_daily_price_matrix()
        returns = self.build_daily_returns()

        latest_prices = prices.dropna(how="all").iloc[-1]
        latest_returns = returns.dropna(how="all").iloc[-1]

        movers = pd.DataFrame({
            "price": latest_prices,
            "return": latest_returns,
        })

        movers = movers.dropna()

        gainers = (
            movers
            .sort_values("return", ascending=False)
            .head(n)
        )

        losers = (
            movers
            .sort_values("return", ascending=True)
            .head(n)
        )

        return gainers, losers

    def return_diagnostics(self) -> dict:
        """
        Inspect the distribution of individual daily returns.
        """

        returns = self.build_daily_returns()

        values = (
            returns
            .stack()
            .dropna()
        )

        if values.empty:
            raise ValueError(
                "No valid returns available."
            )

        return {
            "count": len(values),

            "min": values.min(),
            "max": values.max(),

            "p01": values.quantile(0.01),
            "p05": values.quantile(0.05),
            "p25": values.quantile(0.25),
            "median": values.median(),
            "p75": values.quantile(0.75),
            "p95": values.quantile(0.95),
            "p99": values.quantile(0.99),

            "over_100pct": (values > 1).sum(),
            "over_500pct": (values > 5).sum(),
            "over_1000pct": (values > 10).sum(),

            "under_minus_50pct": (values < -0.5).sum(),
            "under_minus_90pct": (values < -0.9).sum(),
        }

    def market_coverage(self) -> pd.Series:
    #Percentage of tracked assets with a valid price
    #on each day.
        prices = self.build_daily_price_matrix()
        return prices.notna().mean(axis=1) * 100

        # ---------------------------------------------------------
    # CATEGORY INDICES
    # ---------------------------------------------------------

    def category_returns(self) -> dict:
        """
        Calculate equal-weighted daily returns for major
        CS2 market categories.
        """

        returns = self.build_daily_returns()

        categories = {
            "Rifles": [],
            "Knives": [],
            "Gloves": [],
            "Pistols": [],
            "Stickers": [],
            "Cases": [],
        }

        for name in returns.columns:

            name_lower = name.lower()

            if name.startswith("★"):
                if "knife" in name_lower:
                    categories["Knives"].append(name)
                elif "glove" in name_lower:
                    categories["Gloves"].append(name)

            elif "sticker" in name_lower:
                categories["Stickers"].append(name)

            elif "case" in name_lower or "capsule" in name_lower:
                categories["Cases"].append(name)

            else:
                pistols = [
                    "glock-18",
                    "usp-s",
                    "p2000",
                    "p250",
                    "deagle",
                    "five-seven",
                    "tec-9",
                    "cz75-auto",
                    "dual berettas",
                    "r8 revolver"
                ]

                rifles = [
                    "ak-47",
                    "m4a1-s",
                    "m4a4",
                    "awp",
                    "aug",
                    "sg 553",
                    "famas",
                    "galil ar",
                    "ssg 08",
                    "scar-20",
                    "g3sg1"
                ]

                if any(name_lower.startswith(p) for p in pistols):
                    categories["Pistols"].append(name)

                elif any(name_lower.startswith(r) for r in rifles):
                    categories["Rifles"].append(name)

        result = {}

        for category, assets in categories.items():

            if not assets:
                result[category] = float("nan")
                continue

            category_data = returns[assets]

            result[category] = (
                category_data.iloc[-1]
                .dropna()
                .mean()
            )

        return result