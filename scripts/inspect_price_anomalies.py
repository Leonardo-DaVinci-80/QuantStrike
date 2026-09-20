from pathlib import Path

import pyarrow.dataset as ds
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

HISTORICAL_FILE = (
    ROOT
    / "data"
    / "processed"
    / "historical_prices.parquet"
)

METADATA_FILE = (
    ROOT
    / "data"
    / "processed"
    / "skin_metadata.parquet"
)


print("=" * 80)
print("QuantStrike — Lightweight Price Anomaly Investigation")
print("=" * 80)


# ---------------------------------------------------------------------
# Load metadata
# ---------------------------------------------------------------------

metadata = pd.read_parquet(
    METADATA_FILE,
    engine="pyarrow",
    columns=[
        "skin_id",
        "name",
        "condition",
    ],
)

metadata["skin_id"] = (
    metadata["skin_id"]
    .astype(str)
)

lore_metadata = metadata[
    metadata["name"]
    .astype(str)
    .str.contains(
        "Butterfly Knife | Lore",
        case=False,
        regex=False,
        na=False,
    )
    & metadata["condition"]
    .astype(str)
    .eq("Battle-Scarred")
]

lore_ids = set(
    lore_metadata["skin_id"]
    .astype(str)
)

print(
    f"\nBS Lore skin IDs: {len(lore_ids)}"
)

for skin_id in lore_ids:
    print(
        f"  {skin_id}"
    )


# ---------------------------------------------------------------------
# Open Parquet dataset
# ---------------------------------------------------------------------

dataset = ds.dataset(
    HISTORICAL_FILE,
    format="parquet",
)

print("\nHistorical dataset opened.")


# ---------------------------------------------------------------------
# Scan only BS Lore
# ---------------------------------------------------------------------

scanner = dataset.scanner(
    columns=[
        "skin_id",
        "timestamp",
        "price",
        "volume",
    ],
    filter=ds.field("skin_id").isin(
        list(lore_ids)
    ),
)


rows = []

print("\nScanning BS Lore observations...")


for batch in scanner.to_batches():

    batch_df = batch.to_pandas()

    rows.append(
        batch_df
    )


if not rows:
    print("No observations found.")
    raise SystemExit


lore = pd.concat(
    rows,
    ignore_index=True,
)


# ---------------------------------------------------------------------
# Convert timestamp
# ---------------------------------------------------------------------

lore["timestamp"] = pd.to_datetime(
    lore["timestamp"],
    unit="s",
    errors="coerce",
)


lore = lore.sort_values(
    "timestamp"
).reset_index(
    drop=True
)


# ---------------------------------------------------------------------
# Basic statistics
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("BS LORE RESULTS")
print("=" * 80)

print(
    f"Observations: {len(lore):,}"
)

print(
    f"Earliest: {lore['timestamp'].min()}"
)

print(
    f"Latest:   {lore['timestamp'].max()}"
)

print(
    f"Minimum price: ${lore['price'].min():,.4f}"
)

print(
    f"Maximum price: ${lore['price'].max():,.2f}"
)


# ---------------------------------------------------------------------
# Detect isolated crashes
# ---------------------------------------------------------------------

lore["previous_price"] = (
    lore["price"].shift(1)
)

lore["next_price"] = (
    lore["price"].shift(-1)
)

lore["crash_ratio"] = (
    lore["price"]
    / lore["previous_price"]
)

lore["recovery_ratio"] = (
    lore["next_price"]
    / lore["price"]
)

lore["recovery_to_previous"] = (
    lore["next_price"]
    / lore["previous_price"]
)


anomalies = lore[
    lore["previous_price"].notna()
    & lore["next_price"].notna()
    & (
        lore["crash_ratio"]
        < 0.25
    )
    & (
        lore["recovery_ratio"]
        > 2.0
    )
    & (
        lore["recovery_to_previous"]
        > 0.50
    )
].copy()


# ---------------------------------------------------------------------
# Print anomalies
# ---------------------------------------------------------------------

print("\n" + "=" * 80)
print("BS LORE ISOLATED PRICE ANOMALIES")
print("=" * 80)

if anomalies.empty:

    print("No isolated anomalies found.")

else:

    print(
        f"Found {len(anomalies):,} anomalies."
    )

    print()

    print(
        anomalies[
            [
                "timestamp",
                "previous_price",
                "price",
                "next_price",
                "volume",
                "crash_ratio",
                "recovery_ratio",
            ]
        ]
        .to_string(
            index=False
        )
    )

print("\nInvestigation complete.")