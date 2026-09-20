from pathlib import Path
import sys

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "daily_market_data.parquet"
)

OUTPUT_FILE = (
    ROOT
    / "data"
    / "processed"
    / "market_summary.parquet"
)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

QSI_BASE = 1000.0

# We allow irregular observations, but only when the previous
# observation is reasonably recent.
#
# Example:
#   May 1 -> May 5
#
# The observed 50% move is NOT treated as a 50% one-day return.
# Instead, we convert the multi-day return into a daily-equivalent
# log return.
MAX_GAP_DAYS = 7

# Extreme individual observations are capped AFTER converting them
# into daily-equivalent returns.
RETURN_CLIP = 0.50

# Categories used by the Market page.
CATEGORY_KEYWORDS = {
    "Knives": [
        "knife",
        "bayonet",
        "karambit",
        "gut knife",
        "flip knife",
        "huntsman knife",
        "falchion knife",
        "bowie knife",
        "shadow daggers",
        "butterfly knife",
        "navaja knife",
        "stiletto knife",
        "talon knife",
        "ursus knife",
        "classic knife",
        "paracord knife",
        "survival knife",
        "nomad knife",
        "skeleton knife",
        "kukri knife",
    ],
    "Gloves": [
        "gloves",
        "glove",
    ],
    "Rifles": [
        "ak-47",
        "m4a1",
        "m4a1-s",
        "m4a4",
        "aug",
        "famas",
        "galil",
        "sg 553",
        "ssg 08",
        "scar-20",
        "g3sg1",
    ],
    "Pistols": [
        "glock-18",
        "usp-s",
        "p2000",
        "p250",
        "deagle",
        "desert eagle",
        "five-seven",
        "tec-9",
        "cz75",
        "cz75-auto",
        "dual berettas",
        "r8 revolver",
    ],
    "SMGs": [
        "mac-10",
        "mp9",
        "mp7",
        "mp5-sd",
        "ump-45",
        "p90",
        "pp-bizon",
        "mp5",
    ],
    "Heavy": [
        "nova",
        "xm1014",
        "mag-7",
        "sawed-off",
        "m249",
        "negev",
    ],
    "Cases": [
        "case",
        "case hardened",
    ],
    "Stickers": [
        "sticker",
    ],
    "Agents": [
        "agent",
    ],
    "Charms": [
        "charm",
    ],
}


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def classify_category(name: str) -> str:
    """
    Assign an asset to the first matching broad market category.
    """

    text = str(name).lower()

    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return category

    return "Other"


def calculate_daily_equivalent_return(
    current_price: pd.Series,
    previous_price: pd.Series,
    gap_days: pd.Series,
) -> pd.Series:
    """
    Convert an irregular-period price change into a daily-equivalent
    return using logarithmic compounding.

    If:
        previous = 10
        current  = 15
        gap      = 4 days

    We calculate:

        daily_log_return = log(15 / 10) / 4

    and then:

        daily_return = exp(daily_log_return) - 1

    This avoids incorrectly treating the entire 50% move as a
    single-day return.
    """

    ratio = current_price / previous_price

    valid = (
        current_price.gt(0)
        & previous_price.gt(0)
        & gap_days.gt(0)
    )

    result = pd.Series(
        np.nan,
        index=current_price.index,
        dtype="float64",
    )

    result.loc[valid] = (
        np.exp(
            np.log(ratio.loc[valid])
            / gap_days.loc[valid]
        )
        - 1.0
    )

    return result


def build_index(
    daily_returns: pd.DataFrame,
    return_column: str,
    base_value: float = QSI_BASE,
) -> pd.Series:
    """
    Build a compounded index from daily returns.

    The first valid date is explicitly set to the base value.
    """

    returns = (
        daily_returns[
            ["date", return_column]
        ]
        .dropna(subset=[return_column])
        .sort_values("date")
        .drop_duplicates("date", keep="last")
        .reset_index(drop=True)
    )

    if returns.empty:
        return pd.Series(dtype="float64")

    index_values = np.empty(len(returns), dtype="float64")

    index_values[0] = base_value

    if len(returns) > 1:
        index_values[1:] = (
            base_value
            * np.cumprod(
                1.0
                + returns[return_column]
                .iloc[1:]
                .to_numpy()
            )
        )

    return pd.Series(
        index_values,
        index=returns["date"],
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    print("=" * 70)
    print("QuantStrike Market Summary Builder — v2")
    print("=" * 70)

    print(f"\nInput : {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input dataset not found: {INPUT_FILE}"
        )

    # -------------------------------------------------------------
    # Load source data
    # -------------------------------------------------------------

    print("\nLoading daily market dataset...")

    df = pd.read_parquet(
        INPUT_FILE,
        engine="pyarrow",
        columns=[
            "date",
            "asset_id",
            "name",
            "price",
            "observation_count",
        ],
    )

    print(
        f"Loaded {len(df):,} daily observations."
    )

    # -------------------------------------------------------------
    # Clean
    # -------------------------------------------------------------

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df["price"] = pd.to_numeric(
        df["price"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "date",
            "asset_id",
            "price",
        ]
    )

    df = df[df["price"] > 0]

    # One price per asset/day.
    df = (
        df.sort_values(
            ["asset_id", "date"]
        )
        .drop_duplicates(
            subset=["asset_id", "date"],
            keep="last",
        )
        .reset_index(drop=True)
    )

    print(
        f"Clean observations: {len(df):,}"
    )

    # -------------------------------------------------------------
    # Previous observation
    # -------------------------------------------------------------

    print("\nCalculating interval returns...")

    grouped = df.groupby(
        "asset_id",
        sort=False,
    )

    df["previous_price"] = (
        grouped["price"].shift(1)
    )

    df["previous_date"] = (
        grouped["date"].shift(1)
    )

    df["gap_days"] = (
        df["date"]
        - df["previous_date"]
    ).dt.days

    # Only use reasonably recent observations.
    valid_gap = (
        df["gap_days"].ge(1)
        & df["gap_days"].le(MAX_GAP_DAYS)
        & df["previous_price"].notna()
        & df["previous_price"].gt(0)
    )

    returns = df.loc[
        valid_gap,
        [
            "date",
            "asset_id",
            "name",
            "price",
            "previous_price",
            "gap_days",
        ],
    ].copy()

    returns["return"] = calculate_daily_equivalent_return(
        current_price=returns["price"],
        previous_price=returns["previous_price"],
        gap_days=returns["gap_days"],
    )

    returns = returns.dropna(
        subset=["return"]
    )

    # -------------------------------------------------------------
    # Diagnostics BEFORE clipping
    # -------------------------------------------------------------

    print("\nInterval diagnostics")
    print("-" * 70)

    print(
        f"Usable returns:     {len(returns):,}"
    )

    print(
        f"1-day observations: "
        f"{(returns['gap_days'] == 1).sum():,}"
    )

    print(
        f"2-7 day observations: "
        f"{returns['gap_days'].between(2, 7).sum():,}"
    )

    print(
        f"Median gap:         "
        f"{returns['gap_days'].median():.1f} days"
    )

    print(
        f"Mean gap:           "
        f"{returns['gap_days'].mean():.2f} days"
    )

    print(
        f"Raw median daily return: "
        f"{returns['return'].median():+.4%}"
    )

    print(
        f"Raw mean daily return:   "
        f"{returns['return'].mean():+.4%}"
    )

    print(
        f"Raw min daily return:    "
        f"{returns['return'].min():+.4%}"
    )

    print(
        f"Raw max daily return:    "
        f"{returns['return'].max():+.4%}"
    )

    # -------------------------------------------------------------
    # Clip extreme observations
    # -------------------------------------------------------------

    negative_clipped = (
        returns["return"] < -RETURN_CLIP
    ).sum()

    positive_clipped = (
        returns["return"] > RETURN_CLIP
    ).sum()

    returns["return"] = returns["return"].clip(
        -RETURN_CLIP,
        RETURN_CLIP,
    )

    print("\nReturn diagnostics")
    print("-" * 70)

    print(
        f"Negative clipped:   "
        f"{negative_clipped:,}"
    )

    print(
        f"Positive clipped:   "
        f"{positive_clipped:,}"
    )

    print(
        f"Final mean daily return:   "
        f"{returns['return'].mean():+.4%}"
    )

    print(
        f"Final median daily return: "
        f"{returns['return'].median():+.4%}"
    )

    print(
        f"Final daily volatility:     "
        f"{returns['return'].std():.4%}"
    )

    # -------------------------------------------------------------
    # Category classification
    # -------------------------------------------------------------

    print("\nClassifying assets...")

    returns["category"] = returns["name"].map(
        classify_category
    )

    # -------------------------------------------------------------
    # Daily market statistics
    # -------------------------------------------------------------

    print("\nBuilding daily market statistics...")

    grouped_daily = (
        returns.groupby("date")
        .agg(
            market_return=("return", "mean"),
            daily_volatility=("return", "std"),
            active_assets=("asset_id", "nunique"),
        )
        .reset_index()
    )

    # Breadth
    returns["is_advancing"] = (
        returns["return"] > 0
    )

    returns["is_declining"] = (
        returns["return"] < 0
    )

    returns["is_unchanged"] = (
        returns["return"] == 0
    )

    breadth = (
        returns.groupby("date")
        .agg(
            advancing=("is_advancing", "sum"),
            declining=("is_declining", "sum"),
            unchanged=("is_unchanged", "sum"),
        )
        .reset_index()
    )

    daily = grouped_daily.merge(
        breadth,
        on="date",
        how="left",
    )

    # -------------------------------------------------------------
    # Tracked assets + coverage
    # -------------------------------------------------------------

    tracked_assets = (
        returns["asset_id"]
        .nunique()
    )

    daily["tracked_assets"] = tracked_assets

    daily["coverage"] = (
        daily["active_assets"]
        / daily["tracked_assets"]
    )

    # -------------------------------------------------------------
    # QSI
    # -------------------------------------------------------------

    print("\nCalculating QuantStrike Index...")

    qsi = build_index(
        daily,
        "market_return",
    )

    qsi_df = (
        qsi.rename("qsi")
        .reset_index()
        .rename(columns={"index": "date"})
    )

    daily = daily.merge(
        qsi_df,
        on="date",
        how="left",
    )

    # -------------------------------------------------------------
    # Category indices
    # -------------------------------------------------------------

    print("Calculating category indices...")

    category_daily = (
        returns.groupby(
            ["date", "category"]
        )["return"]
        .mean()
        .reset_index()
    )

    category_pivot = (
        category_daily
        .pivot(
            index="date",
            columns="category",
            values="return",
        )
        .sort_index()
    )

    category_index_frames = []

    for category in category_pivot.columns:
        temp = category_pivot[
            [category]
        ].reset_index()

        temp = temp.rename(
            columns={
                category: f"{category}_return"
            }
        )

        index_series = build_index(
            temp,
            f"{category}_return",
        )

        if index_series.empty:
            continue

        index_df = (
            index_series
            .rename(
                f"{category}_index"
            )
            .reset_index()
            .rename(
                columns={
                    "index": "date"
                }
            )
        )

        category_index_frames.append(
            index_df
        )

        # Also keep the daily category return.
        daily = daily.merge(
            temp,
            on="date",
            how="left",
        )

        daily = daily.merge(
            index_df,
            on="date",
            how="left",
        )

    # -------------------------------------------------------------
    # Final ordering / cleanup
    # -------------------------------------------------------------

    daily = (
        daily.sort_values("date")
        .reset_index(drop=True)
    )

    # Convert integer counts explicitly.
    for column in [
        "advancing",
        "declining",
        "unchanged",
        "active_assets",
        "tracked_assets",
    ]:
        daily[column] = (
            daily[column]
            .fillna(0)
            .astype("int32")
        )

    daily["coverage"] = daily[
        "coverage"
    ].astype("float32")

    daily["market_return"] = daily[
        "market_return"
    ].astype("float64")

    daily["daily_volatility"] = daily[
        "daily_volatility"
    ].astype("float64")

    daily["qsi"] = daily[
        "qsi"
    ].astype("float64")

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    print("\nSaving market summary...")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    daily.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        index=False,
    )

    # -------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------

    print("\n" + "=" * 70)
    print("MARKET SUMMARY VALIDATION")
    print("=" * 70)

    print(
        f"Date range:           "
        f"{daily['date'].min().date()} → "
        f"{daily['date'].max().date()}"
    )

    print(
        f"Summary rows:         "
        f"{len(daily):,}"
    )

    print(
        f"Tracked assets:       "
        f"{tracked_assets:,}"
    )

    # QSI
    qsi_initial = (
        daily["qsi"].dropna().iloc[0]
    )

    qsi_final = (
        daily["qsi"].dropna().iloc[-1]
    )

    qsi_min = daily["qsi"].min()
    qsi_max = daily["qsi"].max()

    days_elapsed = (
        daily["date"].iloc[-1]
        - daily["date"].iloc[0]
    ).days

    if days_elapsed > 0:
        qsi_cagr = (
            (qsi_final / qsi_initial)
            ** (365.25 / days_elapsed)
            - 1
        )
    else:
        qsi_cagr = np.nan

    print("\nQSI")
    print("-" * 70)

    print(
        f"Initial:              "
        f"{qsi_initial:,.2f}"
    )

    print(
        f"Final:                "
        f"{qsi_final:,.2f}"
    )

    print(
        f"Minimum:              "
        f"{qsi_min:,.2f}"
    )

    print(
        f"Maximum:              "
        f"{qsi_max:,.2f}"
    )

    print(
        f"CAGR:                 "
        f"{qsi_cagr:+.2%}"
    )

    # Market returns
    annualized_volatility = (
        daily["market_return"]
        .std()
        * np.sqrt(252)
    )

    print("\nMarket returns")
    print("-" * 70)

    print(
        f"Mean daily return:    "
        f"{daily['market_return'].mean():+.4%}"
    )

    print(
        f"Median daily return:  "
        f"{daily['market_return'].median():+.4%}"
    )

    print(
        f"Daily volatility:     "
        f"{daily['market_return'].std():.4%}"
    )

    print(
        f"Annualized volatility:"
        f" {annualized_volatility:.2%}"
    )

    print(
        f"Minimum daily return: "
        f"{daily['market_return'].min():+.4%}"
    )

    print(
        f"Maximum daily return: "
        f"{daily['market_return'].max():+.4%}"
    )

    # Latest session
    latest = daily.iloc[-1]

    print("\nLatest session")
    print("-" * 70)

    print(
        f"Date:                 "
        f"{latest['date'].date()}"
    )

    print(
        f"Market return:        "
        f"{latest['market_return']:+.4%}"
    )

    print(
        f"Advancing:            "
        f"{int(latest['advancing']):,}"
    )

    print(
        f"Declining:            "
        f"{int(latest['declining']):,}"
    )

    print(
        f"Unchanged:            "
        f"{int(latest['unchanged']):,}"
    )

    print(
        f"Active assets:        "
        f"{int(latest['active_assets']):,}"
    )

    print(
        f"Coverage:             "
        f"{latest['coverage']:.2%}"
    )

    print("\n" + "=" * 70)
    print("Market summary build complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()