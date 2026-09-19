from pathlib import Path
import sys
import re
import time

import pandas as pd


# ============================================================
# Project paths
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

RAW_ITEMS_DIRECTORY = ROOT / "data" / "raw" / "items"
INDEX_FILE = ROOT / "data" / "raw" / "name_conversion_table.csv"

PROCESSED_DIRECTORY = ROOT / "data" / "processed"

HISTORICAL_OUTPUT = PROCESSED_DIRECTORY / "historical_prices.parquet"
METADATA_OUTPUT = PROCESSED_DIRECTORY / "skin_metadata.parquet"


# ============================================================
# Configuration
# ============================================================

MIN_PLAUSIBLE_PRICE = 0.001

REQUIRED_COLUMNS = {
    "price",
    "quantity",
    "unix timestamp",
}


# ============================================================
# Helpers
# ============================================================


def metadata_filename_for(raw_filename: str) -> str:
    return raw_filename.replace("�", "ö") # fixes AUG | Flame Jörmungandr issue where ö was �

def parse_name(name: str) -> dict:
    """
    Parse a CS2 item name into its component fields.

    Supports:
    - Normal skins
    - StatTrak™ skins
    - ★ StatTrak™ knife/glove skins
    - Souvenir skins
    - Vanilla items
    """

    original = name.strip()

    stattrak = (
        original.startswith("StatTrak™")
        or original.startswith("★ StatTrak™")
    )

    souvenir = original.startswith("Souvenir")

    cleaned = original

    # Remove StatTrak prefix.
    if cleaned.startswith("★ StatTrak™ "):
        cleaned = cleaned[len("★ StatTrak™ "):]

    elif cleaned.startswith("StatTrak™ "):
        cleaned = cleaned[len("StatTrak™ "):]

    # Remove Souvenir prefix.
    if cleaned.startswith("Souvenir "):
        cleaned = cleaned[len("Souvenir "):]

    # Extract wear condition from the end.
    condition_match = re.search(
        r"\(([^()]*)\)$",
        cleaned,
    )

    if condition_match:
        condition = condition_match.group(1)
        item_name = cleaned[:condition_match.start()].strip()
    else:
        condition = "Vanilla"
        item_name = cleaned

    # Vanilla items such as cases, agents, etc.
    if " | " not in item_name:
        return {
            "weapon": item_name,
            "finish": item_name,
            "condition": condition,
            "stattrak": stattrak,
            "souvenir": souvenir,
        }

    weapon, finish = item_name.split(" | ", 1)

    return {
        "weapon": weapon.strip(),
        "finish": finish.strip(),
        "condition": condition,
        "stattrak": stattrak,
        "souvenir": souvenir,
    }

def get_base_name(name: str) -> str:
    """
    Remove StatTrak/Souvenir prefixes and wear condition.
    """

    return (
        name
        .replace("StatTrak™ ", "")
        .replace("Souvenir ", "")
        .rsplit(" (", 1)[0]
    )


def load_index() -> pd.DataFrame:
    """
    Load the name conversion table and construct metadata.
    """

    if not INDEX_FILE.exists():
        raise FileNotFoundError(
            f"Index file not found:\n{INDEX_FILE}"
        )

    index = pd.read_csv(INDEX_FILE)

    required = {
        "URL encoded name",
        "decoded name",
    }

    missing = required - set(index.columns)

    if missing:
        raise ValueError(
            f"Index is missing required columns: {sorted(missing)}"
        )

    index = index.copy()

    index["name"] = index["decoded name"]
    index["file_name"] = (
        index["URL encoded name"].astype(str) + ".csv"
    )

    index["base_name"] = index["name"].map(get_base_name)

    attributes = index["name"].map(parse_name)

    index["weapon"] = attributes.map(lambda x: x["weapon"])
    index["finish"] = attributes.map(lambda x: x["finish"])
    index["condition"] = attributes.map(lambda x: x["condition"])
    index["stattrak"] = attributes.map(lambda x: x["stattrak"])
    index["souvenir"] = attributes.map(lambda x: x["souvenir"])

    return index[
        [
            "file_name",
            "name",
            "base_name",
            "weapon",
            "finish",
            "condition",
            "stattrak",
            "souvenir",
        ]
    ]


# ============================================================
# Main processing
# ============================================================

def main() -> None:

    print("=" * 70)
    print("QuantStrike Historical Data Builder")
    print("=" * 70)

    if not RAW_ITEMS_DIRECTORY.exists():
        raise FileNotFoundError(
            f"Raw items directory not found:\n"
            f"{RAW_ITEMS_DIRECTORY}"
        )

    PROCESSED_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print()
    print(f"Raw dataset:       {RAW_ITEMS_DIRECTORY}")
    print(f"Index:             {INDEX_FILE}")
    print(f"Output directory:  {PROCESSED_DIRECTORY}")
    print()

    # --------------------------------------------------------
    # Load metadata index
    # --------------------------------------------------------

    print("Loading name conversion table...")

    metadata = load_index()

    print(
        f"Found {len(metadata):,} indexed items."
    )

    # --------------------------------------------------------
    # Discover CSV files
    # --------------------------------------------------------

    print()
    print("Scanning historical CSV files...")

    files = list(
        RAW_ITEMS_DIRECTORY.glob("*.csv")
    )

    print(
        f"Found {len(files):,} CSV files."
    )

    # --------------------------------------------------------
    # Match metadata to files
    # --------------------------------------------------------

    metadata_by_file = metadata.set_index(
        "file_name"
    )

    # --------------------------------------------------------
    # Process histories
    # --------------------------------------------------------

    historical_chunks = []

    processed = 0
    skipped = 0
    total_rows = 0

    start_time = time.time()

    for filepath in files:

        try:
            metadata_filename = metadata_filename_for(filepath.name)

            if metadata_filename not in metadata_by_file.index:
                skipped += 1
                continue

            df = pd.read_csv(
                filepath,
                usecols=[
                    "price",
                    "quantity",
                    "unix timestamp",
            ])

            missing = REQUIRED_COLUMNS - set(df.columns)

            if missing:
                print(
                    f"[SKIP] {filepath.name}: "
                    f"missing {sorted(missing)}"
                )

                skipped += 1
                continue

            # ------------------------------------------------
            # Numeric conversion
            # ------------------------------------------------

            df["price"] = pd.to_numeric(
                df["price"],
                errors="coerce",
            )

            df["quantity"] = pd.to_numeric(
                df["quantity"],
                errors="coerce",
            )

            df["unix timestamp"] = pd.to_numeric(
                df["unix timestamp"],
                errors="coerce",
            )

            # ------------------------------------------------
            # Validation
            # ------------------------------------------------

            df = df.dropna(
                subset=[
                    "price",
                    "quantity",
                    "unix timestamp",
                ]
            )

            df = df[
                (df["price"] >= MIN_PLAUSIBLE_PRICE)
                & (df["quantity"] >= 0)
            ]

            if df.empty:
                skipped += 1
                continue

            # ------------------------------------------------
            # Rename columns
            # ------------------------------------------------

            df = df.rename(
                columns={
                    "unix timestamp": "timestamp",
                    "quantity": "volume",
                }
            )

            # ------------------------------------------------
            # Add skin identifier
            # ------------------------------------------------

            df["skin_id"] = metadata_filename

            df = df[
                [
                    "skin_id",
                    "timestamp",
                    "price",
                    "volume",
                ]
            ]

            historical_chunks.append(df)

            processed += 1
            total_rows += len(df)

            # ------------------------------------------------
            # Progress
            # ------------------------------------------------

            if processed % 100 == 0:

                elapsed = time.time() - start_time

                rate = (
                    processed / elapsed
                    if elapsed > 0
                    else 0
                )

                print(
                    f"Processed {processed:,}/{len(files):,} "
                    f"files | "
                    f"{total_rows:,} rows | "
                    f"{rate:.1f} files/sec"
                )

        except Exception as exc:

            print(
                f"[SKIP] {filepath.name}: {exc}"
            )

            skipped += 1

    # --------------------------------------------------------
    # Check results
    # --------------------------------------------------------

    if not historical_chunks:

        raise RuntimeError(
            "No valid historical data was processed."
        )

    print()
    print("Combining historical data...")

    historical = pd.concat(
        historical_chunks,
        ignore_index=True,
    )

    # --------------------------------------------------------
    # Optimize dtypes
    # --------------------------------------------------------

    historical["skin_id"] = (
        historical["skin_id"].astype("string")
    )

    historical["timestamp"] = (
        pd.to_numeric(
            historical["timestamp"],
            downcast="integer",
        )
    )

    historical["price"] = (
        pd.to_numeric(
            historical["price"],
            downcast="float",
        )
    )

    historical["volume"] = (
        pd.to_numeric(
            historical["volume"],
            downcast="integer",
        )
    )

    # --------------------------------------------------------
    # Sort once
    # --------------------------------------------------------

    print("Sorting historical data...")

    historical = historical.sort_values(
        [
            "skin_id",
            "timestamp",
        ],
        kind="stable",
    ).reset_index(drop=True)

    # --------------------------------------------------------
    # Calculate latest values
    # --------------------------------------------------------

    print("Calculating latest prices...")

    latest = (
        historical
        .drop_duplicates(
            subset=["skin_id"],
            keep="last",
        )
        [
            [
                "skin_id",
                "price",
                "timestamp",
            ]
        ]
        .rename(
            columns={
                "price": "latest_price",
                "timestamp": "latest_timestamp",
            }
        )
    )

    # --------------------------------------------------------
    # Attach latest prices to metadata
    # --------------------------------------------------------

    metadata = metadata.copy()

    metadata["skin_id"] = metadata["file_name"]

    metadata = metadata.merge(
        latest,
        on="skin_id",
        how="left",
    )

    metadata["latest_price"] = (
        metadata["latest_price"]
        .fillna(0.0)
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    print()
    print("Writing historical Parquet file...")

    historical.to_parquet(
        HISTORICAL_OUTPUT,
        index=False,
    )

    print("Writing metadata Parquet file...")

    metadata.to_parquet(
        METADATA_OUTPUT,
        index=False,
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    elapsed = time.time() - start_time

    print()
    print("=" * 70)
    print("BUILD COMPLETE")
    print("=" * 70)

    print(
        f"Files discovered:       {len(files):,}"
    )

    print(
        f"Files processed:        {processed:,}"
    )

    print(
        f"Files skipped:          {skipped:,}"
    )

    print(
        f"Historical rows:        {len(historical):,}"
    )

    print(
        f"Unique skins:           "
        f"{historical['skin_id'].nunique():,}"
    )

    print(
        f"Processing time:        "
        f"{elapsed / 60:.2f} minutes"
    )

    print()
    print(
        f"Historical output:\n{HISTORICAL_OUTPUT}"
    )

    print(
        f"Metadata output:\n{METADATA_OUTPUT}"
    )

    print()
    print("Done.")


if __name__ == "__main__":
    main()