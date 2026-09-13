from typing import Dict, List
from pathlib import Path
from time import perf_counter

import pandas as pd

from backend.collectors.csv_collector import CSVCollector
from backend.models.price_point import PricePoint
from backend.repositories.skin_repository import SkinRepository


class MarketOverviewAnalyzer:
    """
    Market-wide analytics for QuantStrike.

    V3 features:
    - Daily price matrix
    - Observation matrix
    - Asset-relative rolling/expanding z-score filtering
    - Rejection diagnostics
    - Continuous QSI
    - Category indices
    - Category returns
    - Market breadth
    - Performance-aware disk caching

    Important:
    - Missing observations are NOT treated as zero returns.
    - Prices are carried forward only to calculate a return when an
      asset next receives a genuine observation.
    - Outlier detection occurs BEFORE QSI return clipping.
    """

    CACHE_VERSION = "qsi_v3_1_robust"

    def __init__(
        self,
        repository: SkinRepository,
        min_observations: int = 30,
        z_threshold: float = 5.0,
        rolling_window: int = 30,
        min_z_observations: int = 10,
        use_disk_cache: bool = True,
    ):
        self.repository = repository
        self.min_observations = min_observations

        # V3 outlier configuration
        self.z_threshold = abs(float(z_threshold))
        self.rolling_window = int(rolling_window)
        self.min_z_observations = int(min_z_observations)

        self.use_disk_cache = use_disk_cache

        self._histories: Dict[str, List[PricePoint]] | None = None

        self._daily_prices: pd.DataFrame | None = None
        self._observations: pd.DataFrame | None = None
        self._raw_returns: pd.DataFrame | None = None
        self._daily_returns: pd.DataFrame | None = None

        self._outlier_log: pd.DataFrame | None = None

        self._load_time = None
        self._processing_time = None

    # =========================================================
    # CACHE
    # =========================================================

    @property
    def cache_path(self) -> Path:
        """
        Disk cache for processed market data.

        The cache lives beside the demo item data.
        """

        items_directory = Path(
            self.repository.items_directory
        )

        cache_directory = (
            items_directory.parent /
            "market_cache"
        )

        cache_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        return (
            cache_directory /
            f"market_{self.CACHE_VERSION}.pkl"
        )

    def _load_disk_cache(self) -> bool:
        """
        Load processed market matrices from disk if available.
        """

        if not self.use_disk_cache:
            return False

        path = self.cache_path

        if not path.exists():
            return False

        try:
            cached = pd.read_pickle(path)

            required_keys = {
                "prices",
                "observations",
                "raw_returns",
                "daily_returns",
                "outlier_log",
            }

            if not required_keys.issubset(cached.keys()):
                return False

            self._daily_prices = cached["prices"]
            self._observations = cached["observations"]
            self._raw_returns = cached["raw_returns"]
            self._daily_returns = cached["daily_returns"]
            self._outlier_log = cached["outlier_log"]

            return True

        except Exception as exc:
            print(
                f"[MarketOverview] Cache load failed: {exc}"
            )
            return False

    def _save_disk_cache(self):
        """
        Save processed market matrices to disk.
        """

        if not self.use_disk_cache:
            return

        if self._daily_prices is None:
            return

        payload = {
            "prices": self._daily_prices,
            "observations": self._observations,
            "raw_returns": self._raw_returns,
            "daily_returns": self._daily_returns,
            "outlier_log": self._outlier_log,
        }

        try:
            self.cache_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            pd.to_pickle(
                payload,
                self.cache_path
            )

            print(
                f"[MarketOverview] Saved cache: "
                f"{self.cache_path}"
            )

        except Exception as exc:
            print(
                f"[MarketOverview] Cache save failed: {exc}"
            )

    # =========================================================
    # DATA LOADING
    # =========================================================

    def load_histories(self) -> Dict[str, List[PricePoint]]:
        """
        Load valid historical price data for all tracked assets.
        """

        if self._histories is not None:
            return self._histories

        start = perf_counter()

        histories = {}

        for _, row in self.repository.index.iterrows():

            name = row["name"]

            filepath = (
                f"{self.repository.items_directory}/"
                f"{row['file_name']}"
            )

            try:
                history = CSVCollector.load_history(filepath)

            except (
                FileNotFoundError,
                ValueError,
                OSError,
            ):
                continue

            if len(history) < self.min_observations:
                continue

            histories[name] = history

        self._histories = histories

        self._load_time = perf_counter() - start

        print(
            f"[MarketOverview] Loaded "
            f"{len(histories):,} histories in "
            f"{self._load_time:.2f}s"
        )

        return histories

    # =========================================================
    # DAILY MARKET DATA
    # =========================================================

    def _build_daily_market_data(self):
        """
        Build daily prices and observation matrix.

        If a processed disk cache exists, use it instead of
        rebuilding all historical CSVs.
        """

        if (
            self._daily_prices is not None
            and self._observations is not None
        ):
            return (
                self._daily_prices,
                self._observations,
            )

        # -----------------------------------------------------
        # Try disk cache first
        # -----------------------------------------------------

        if self._load_disk_cache():

            print(
                "[MarketOverview] "
                "Loaded processed market data from cache."
            )

            return (
                self._daily_prices,
                self._observations,
            )

        start = perf_counter()

        histories = self.load_histories()

        price_series = []
        observation_series = []

        for name, history in histories.items():

            if not history:
                continue

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
                df["timestamp"],
                errors="coerce"
            )

            df["price"] = pd.to_numeric(
                df["price"],
                errors="coerce"
            )

            # Basic sanity filtering.
            df = (
                df
                .dropna(
                    subset=[
                        "timestamp",
                        "price",
                    ]
                )
                .sort_values("timestamp")
            )

            df = df[
                df["price"] > 0
            ]

            if df.empty:
                continue

            # -------------------------------------------------
            # Daily price
            # -------------------------------------------------

            daily_price = (
                df
                .set_index("timestamp")["price"]
                .resample("D")
                .last()
            )

            daily_price.name = name

            price_series.append(
                daily_price
            )

            # -------------------------------------------------
            # Daily observation
            # -------------------------------------------------

            daily_observation = (
                df
                .set_index("timestamp")["price"]
                .resample("D")
                .size()
                .gt(0)
            )

            daily_observation.name = name

            observation_series.append(
                daily_observation
            )

        if not price_series:
            raise ValueError(
                "No valid price histories available."
            )

        # -----------------------------------------------------
        # Combine
        # -----------------------------------------------------

        prices = (
            pd.concat(
                price_series,
                axis=1
            )
            .sort_index()
        )

        observations = (
            pd.concat(
                observation_series,
                axis=1
            )
            .reindex(
                index=prices.index,
                columns=prices.columns,
                fill_value=False,
            )
            .fillna(False)
            .astype(bool)
        )

        self._daily_prices = prices
        self._observations = observations

        self._processing_time = (
            perf_counter() - start
        )

        print(
            "[MarketOverview] Built daily market data "
            f"in {self._processing_time:.2f}s"
        )

        return prices, observations

    # =========================================================
    # DAILY PRICE MATRIX
    # =========================================================

    def build_daily_price_matrix(self) -> pd.DataFrame:
        prices, _ = (
            self._build_daily_market_data()
        )

        return prices

    # =========================================================
    # OBSERVATION MATRIX
    # =========================================================

    def build_observation_matrix(self) -> pd.DataFrame:
        _, observations = (
            self._build_daily_market_data()
        )

        return observations

    # =========================================================
    # RAW RETURNS
    # =========================================================

    def _build_raw_returns(self) -> pd.DataFrame:
        """
        Build returns BEFORE outlier filtering.

        Missing days are handled by carrying forward the latest
        known price, but the return is only retained when the
        asset actually received a new observation.
        """

        if self._raw_returns is not None:
            return self._raw_returns

        prices = self.build_daily_price_matrix()
        observations = self.build_observation_matrix()

        # Carry latest known price forward.
        filled_prices = prices.ffill()

        # Return from previous known observation.
        returns = filled_prices.pct_change()

        # Only genuine new observations contribute.
        returns = returns.where(
            observations
        )

        # Do not calculate returns before the first price.
        returns = returns.where(
            filled_prices.notna()
        )

        self._raw_returns = returns

        return returns

    # =========================================================
    # V3 OUTLIER FILTER
    # =========================================================

    def _filter_outliers(
        self,
        returns: pd.DataFrame,
    ) -> pd.DataFrame:
        """
        V3 adaptive outlier detection.

        For every asset:

        1. Calculate a baseline using previous observations.
        2. Prefer a 30-observation rolling window.
        3. Fall back to expanding statistics when insufficient
           rolling observations exist.
        4. Calculate z-score.
        5. Reject observations where:
               z < -threshold
               OR
               z > +threshold

        The current observation is excluded from the statistical
        baseline using shift(1), preventing the outlier itself
        from diluting its own z-score.
        """

        cleaned = returns.copy()

        rejection_rows = []

        for name in returns.columns:

            series = returns[name]

            if series.dropna().empty:
                continue

            # -------------------------------------------------
            # Previous observations only
            # -------------------------------------------------

            previous = series.shift(1)

            rolling_mean = (
                previous
                .rolling(
                    window=self.rolling_window,
                    min_periods=self.min_z_observations,
                )
                .mean()
            )

            rolling_std = (
                previous
                .rolling(
                    window=self.rolling_window,
                    min_periods=self.min_z_observations,
                )
                .std()
            )

            # -------------------------------------------------
            # Expanding fallback
            # -------------------------------------------------

            expanding_mean = (
                previous
                .expanding(
                    min_periods=self.min_z_observations
                )
                .mean()
            )

            expanding_std = (
                previous
                .expanding(
                    min_periods=self.min_z_observations
                )
                .std()
            )

            mean = rolling_mean.fillna(
                expanding_mean
            )

            std = rolling_std.fillna(
                expanding_std
            )

            # -------------------------------------------------
            # Avoid division by zero
            # -------------------------------------------------

            valid_std = (
                std.notna()
                & (std > 0)
            )

            z_scores = pd.Series(
                float("nan"),
                index=series.index
            )

            z_scores.loc[valid_std] = (
                (
                    series.loc[valid_std]
                    - mean.loc[valid_std]
                )
                /
                std.loc[valid_std]
            )

            # -------------------------------------------------
            # Identify extreme observations
            # -------------------------------------------------

            negative_outlier = (
                z_scores < -self.z_threshold
            )

            positive_outlier = (
                z_scores > self.z_threshold
            )

            outliers = (
                negative_outlier
                | positive_outlier
            )

            outliers = outliers.fillna(False)

            # -------------------------------------------------
            # Record rejected observations
            # -------------------------------------------------

            for timestamp in series.index[
                outliers
            ]:

                return_value = series.loc[
                    timestamp
                ]

                z_value = z_scores.loc[
                    timestamp
                ]

                rejection_rows.append(
                    {
                        "item": name,
                        "timestamp": timestamp,
                        "return": return_value,
                        "z_score": z_value,
                        "direction": (
                            "negative"
                            if z_value < 0
                            else "positive"
                        ),
                        "reason": (
                            f"|z| > "
                            f"{self.z_threshold:g}"
                        ),
                    }
                )

            # -------------------------------------------------
            # Remove outliers
            # -------------------------------------------------

            cleaned.loc[
                outliers,
                name
            ] = pd.NA

        # -----------------------------------------------------
        # Diagnostics
        # -----------------------------------------------------

        if rejection_rows:

            self._outlier_log = pd.DataFrame(
                rejection_rows
            )

        else:

            self._outlier_log = pd.DataFrame(
                columns=[
                    "item",
                    "timestamp",
                    "return",
                    "z_score",
                    "direction",
                    "reason",
                ]
            )

        return cleaned

    # =========================================================
    # DAILY RETURNS
    # =========================================================

    def build_daily_returns(self) -> pd.DataFrame:
        """
        Return cleaned daily asset returns.

        V3 cleaning happens BEFORE the ±50% market protection
        cap.

        The ±50% cap remains as a secondary safeguard against
        extreme but statistically undetected observations.
        """

        if self._daily_returns is not None:
            return self._daily_returns

        raw_returns = (
            self._build_raw_returns()
        )

        # -----------------------------------------------------
        # V3 adaptive outlier filtering
        # -----------------------------------------------------

        cleaned = self._filter_outliers(
            raw_returns
        )

        # -----------------------------------------------------
        # Secondary market safety boundary
        # -----------------------------------------------------

        cleaned = cleaned.clip(
            lower=-0.50,
            upper=0.50
        )

        self._daily_returns = cleaned

        # Save processed data after the expensive work.
        self._save_disk_cache()

        return cleaned

    # =========================================================
    # OUTLIER DIAGNOSTICS
    # =========================================================

    def outlier_diagnostics(self) -> dict:
        """
        Return summary statistics for rejected observations.
        """

        # Ensure filtering has happened.
        self.build_daily_returns()

        if self._outlier_log is None:
            return {
                "rejected_count": 0,
                "negative_count": 0,
                "positive_count": 0,
            }

        log = self._outlier_log

        if log.empty:
            return {
                "rejected_count": 0,
                "negative_count": 0,
                "positive_count": 0,
            }

        return {
            "rejected_count": len(log),
            "negative_count": int(
                (log["direction"] == "negative").sum()
            ),
            "positive_count": int(
                (log["direction"] == "positive").sum()
            ),
        }

    def rejected_observations(
        self,
        n: int = 50,
    ) -> pd.DataFrame:
        """
        Return the most extreme rejected observations.
        """

        self.build_daily_returns()

        if (
            self._outlier_log is None
            or self._outlier_log.empty
        ):
            return pd.DataFrame(
                columns=[
                    "item",
                    "timestamp",
                    "return",
                    "z_score",
                    "direction",
                    "reason",
                ]
            )

        return (
            self._outlier_log
            .assign(
                abs_z=lambda df:
                df["z_score"].abs()
            )
            .sort_values(
                "abs_z",
                ascending=False
            )
            .drop(
                columns=["abs_z"]
            )
            .head(n)
        )

    # =========================================================
    # QSI
    # =========================================================

    def calculate_qsi(self) -> pd.Series:
        """
        Calculate the QuantStrike Index.

        Method:

        - Base = 1,000
        - Equal-weighted active-asset returns
        - Only genuine observations contribute
        - Cleaned returns are used
        - Individual returns capped at ±50%
        - Days with no observations carry the previous QSI level
        """

        returns = self.build_daily_returns()

        if returns.empty:
            raise ValueError(
                "No market return data available."
            )

        market_returns = (
            returns
            .mean(
                axis=1,
                skipna=True
            )
        )

        # Days with no observations have no new information.
        # Their market return is 0 ONLY for index continuity;
        # this does not mean stale assets contributed 0%.
        market_returns = (
            market_returns
            .fillna(0.0)
        )

        qsi = (
            1000 *
            (1 + market_returns)
            .cumprod()
        )

        qsi = qsi.replace(
            [float("inf"), float("-inf")],
            pd.NA
        ).dropna()

        qsi.name = "QSI"

        return qsi

    # =========================================================
    # MARKET SNAPSHOT
    # =========================================================

    def latest_market_snapshot(self) -> dict:
        """
        Latest market statistics based only on assets with
        genuine observations.
        """

        returns = self.build_daily_returns()

        if returns.empty:
            raise ValueError(
                "No market return data available."
            )

        valid_returns = (
            returns
            .dropna(how="all")
        )

        if valid_returns.empty:
            raise ValueError(
                "No market return data available."
            )

        latest = (
            valid_returns
            .iloc[-1]
            .dropna()
        )

        if latest.empty:
            raise ValueError(
                "No valid returns in latest market session."
            )

        tracked_assets = len(
            returns.columns
        )

        active_assets = len(latest)

        coverage = (
            active_assets / tracked_assets
            if tracked_assets > 0
            else 0.0
        )

        return {
            "market_return": latest.mean(),
            "advancing": int(
                (latest > 0).sum()
            ),
            "declining": int(
                (latest < 0).sum()
            ),
            "unchanged": int(
                (latest == 0).sum()
            ),
            "volatility": (
                latest.std()
                if len(latest) > 1
                else 0.0
            ),
            "active_assets": active_assets,
            "tracked_assets": tracked_assets,
            "coverage": coverage,
        }

    # =========================================================
    # MARKET BREADTH
    # =========================================================

    def market_breadth(self) -> pd.DataFrame:

        returns = self.build_daily_returns()

        advancing = (
            returns > 0
        ).sum(axis=1)

        declining = (
            returns < 0
        ).sum(axis=1)

        unchanged = (
            returns == 0
        ).sum(axis=1)

        active = (
            returns.notna()
            .sum(axis=1)
        )

        return pd.DataFrame(
            {
                "advancing": advancing,
                "declining": declining,
                "unchanged": unchanged,
                "active": active,
            }
        )

    # =========================================================
    # TOP MOVERS
    # =========================================================

    def top_movers(self, n: int = 10):

        prices = (
            self.build_daily_price_matrix()
        )

        returns = (
            self.build_daily_returns()
        )

        # Latest actual price available.
        latest_prices = (
            prices
            .ffill()
            .iloc[-1]
        )

        # Latest actual cleaned return session.
        valid_returns = (
            returns
            .dropna(how="all")
        )

        if valid_returns.empty:
            empty = pd.DataFrame(
                columns=[
                    "price",
                    "return",
                    "category",
                ]
            )
            return empty, empty

        latest_returns = (
            valid_returns
            .iloc[-1]
        )

        movers = pd.DataFrame(
            {
                "price": latest_prices,
                "return": latest_returns,
            }
        ).dropna()

        movers["category"] = [
            self.classify_asset(name)
            for name in movers.index
        ]

        gainers = (
            movers
            .sort_values(
                "return",
                ascending=False
            )
            .head(n)
        )

        losers = (
            movers
            .sort_values(
                "return",
                ascending=True
            )
            .head(n)
        )

        return gainers, losers

    # =========================================================
    # MARKET COVERAGE
    # =========================================================

    def market_coverage(self) -> pd.Series:

        observations = (
            self.build_observation_matrix()
        )

        return (
            observations
            .mean(axis=1)
            * 100
        )

    # =========================================================
    # RETURN DIAGNOSTICS
    # =========================================================

    def return_diagnostics(self) -> dict:

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
            "over_100pct": (
                values > 1
            ).sum(),
            "over_500pct": (
                values > 5
            ).sum(),
            "over_1000pct": (
                values > 10
            ).sum(),
            "under_minus_50pct": (
                values < -0.5
            ).sum(),
            "under_minus_90pct": (
                values < -0.9
            ).sum(),
        }

    # =========================================================
    # CATEGORY CLASSIFICATION
    # =========================================================

    def classify_asset(self, name: str) -> str:

        lower = name.lower().strip()

        # -----------------------------------------------------
        # Special item types
        # -----------------------------------------------------

        if "sticker" in lower:
            return "Stickers"

        if "capsule" in lower:
            return "Capsules"

        if "graffiti" in lower:
            return "Graffiti"

        if "patch" in lower:
            return "Patches"

        if "music kit" in lower:
            return "Music Kits"

        if "agent" in lower:
            return "Agents"

        if "case" in lower:
            return "Cases"

        if "key" in lower:
            return "Keys"

        # -----------------------------------------------------
        # Knives
        # -----------------------------------------------------

        knife_names = [
            "bayonet",
            "bowie knife",
            "butterfly knife",
            "classic knife",
            "falchion knife",
            "flip knife",
            "gut knife",
            "huntsman knife",
            "karambit",
            "kukri knife",
            "m9 bayonet",
            "navaja knife",
            "nomad knife",
            "paracord knife",
            "shadow daggers",
            "skeleton knife",
            "stiletto knife",
            "survival knife",
            "talon knife",
            "ursus knife",
        ]

        if any(
            knife in lower
            for knife in knife_names
        ):
            return "Knives"

        # -----------------------------------------------------
        # Gloves
        # -----------------------------------------------------

        glove_names = [
            "hand wraps",
            "driver gloves",
            "specialist gloves",
            "sport gloves",
            "moto gloves",
            "hydra gloves",
            "bloodhound gloves",
        ]

        if any(
            glove in lower
            for glove in glove_names
        ):
            return "Gloves"

        # -----------------------------------------------------
        # Pistols
        # -----------------------------------------------------

        pistols = [
            "glock-18",
            "usp-s",
            "p2000",
            "p250",
            "desert eagle",
            "five-seven",
            "tec-9",
            "cz75-auto",
            "dual berettas",
            "r8 revolver",
        ]

        if any(
            lower.startswith(pistol)
            for pistol in pistols
        ):
            return "Pistols"

        # -----------------------------------------------------
        # Rifles
        # -----------------------------------------------------

        rifles = [
            "ak-47",
            "m4a1-s",
            "m4a4",
            "aug",
            "sg 553",
            "famas",
            "galil ar",
            "ssg 08",
            "scar-20",
            "g3sg1",
            "awp",
        ]

        if any(
            lower.startswith(rifle)
            for rifle in rifles
        ):
            return "Rifles"

        # -----------------------------------------------------
        # SMGs
        # -----------------------------------------------------

        smgs = [
            "mac-10",
            "mp5-sd",
            "mp7",
            "mp9",
            "p90",
            "pp-bizon",
            "ump-45",
        ]

        if any(
            lower.startswith(smg)
            for smg in smgs
        ):
            return "SMGs"

        # -----------------------------------------------------
        # Heavy weapons
        # -----------------------------------------------------

        heavy = [
            "nova",
            "xm1014",
            "mag-7",
            "sawed-off",
            "m249",
            "negev",
        ]

        if any(
            lower.startswith(weapon)
            for weapon in heavy
        ):
            return "Heavy Weapons"

        return "Other"

    # =========================================================
    # CATEGORY RETURNS
    # =========================================================

    def category_returns(self) -> dict:

        returns = self.build_daily_returns()

        valid_returns = (
            returns
            .dropna(how="all")
        )

        if valid_returns.empty:
            return {}

        latest = (
            valid_returns
            .iloc[-1]
        )

        categories = {}

        for name in returns.columns:

            category = (
                self.classify_asset(name)
            )

            categories.setdefault(
                category,
                []
            ).append(name)

        result = {}

        for category, assets in categories.items():

            values = (
                latest[assets]
                .dropna()
            )

            if values.empty:

                result[category] = float(
                    "nan"
                )

            else:

                result[category] = (
                    values.mean()
                )

        return result

    # =========================================================
    # CATEGORY INDICES
    # =========================================================

    def category_indices(self) -> dict:
        """
        Calculate category-level indices.

        Each category starts at 1,000.

        Only active assets contribute to the category return.
        Days without observations carry the previous index level.
        """

        returns = self.build_daily_returns()

        category_assets = {}

        for name in returns.columns:

            category = (
                self.classify_asset(name)
            )

            category_assets.setdefault(
                category,
                []
            ).append(name)

        indices = {}

        for category, assets in category_assets.items():

            category_returns = (
                returns[assets]
                .mean(
                    axis=1,
                    skipna=True
                )
                .fillna(0.0)
            )

            if category_returns.empty:
                continue

            indices[category] = (
                1000 *
                (1 + category_returns)
                .cumprod()
            )

        return indices