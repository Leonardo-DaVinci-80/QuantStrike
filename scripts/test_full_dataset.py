from pathlib import Path
from collections import Counter
import pandas as pd
from backend.collectors.csv_collector import CSVCollector


INDEX_FILE = Path("data/raw/name_conversion_table.csv")
ITEMS_DIRECTORY = Path("data/raw/items")


index = pd.read_csv(INDEX_FILE)
index["file_name"] = index["URL encoded name"] + ".csv"


total = len(index)
missing_files = []
empty_histories = []
invalid_histories = []
observation_counts = []
all_timestamps = []
all_prices = []
all_volumes = []

print(f"Scanning {total:,} assets...\n")


for i, row in index.iterrows():
    filename = row["file_name"]
    filepath = ITEMS_DIRECTORY / filename

    if not filepath.exists():
        missing_files.append(filename)
        continue

    try:
        history = CSVCollector.load_history(str(filepath))
    except Exception as e:
        invalid_histories.append((filename, str(e)))
        continue

    if not history:
        empty_histories.append(filename)
        continue

    observation_counts.append(len(history))

    all_timestamps.extend(point.timestamp for point in history)
    all_prices.extend(point.price for point in history)

    for point in history:
        if point.volume is not None:
            all_volumes.append(point.volume)

    if (i + 1) % 1000 == 0:
        print(f"Processed {i + 1:,} / {total:,}")


print("\n" + "=" * 60)
print("FULL DATASET VALIDATION")
print("=" * 60)

print(f"\nAssets in conversion table: {total:,}")
print(f"Missing history files:     {len(missing_files):,}")
print(f"Invalid histories:         {len(invalid_histories):,}")
print(f"Empty histories:            {len(empty_histories):,}")

valid_assets = (
    total
    - len(missing_files)
    - len(invalid_histories)
    - len(empty_histories)
)

print(f"Valid assets:               {valid_assets:,}")
print(f"Valid asset coverage:       {valid_assets / total * 100:.2f}%")


if observation_counts:
    observations = pd.Series(observation_counts)

    print("\nOBSERVATIONS PER ASSET")
    print("-" * 40)
    print(f"Total observations:         {observations.sum():,}")
    print(f"Average:                    {observations.mean():,.1f}")
    print(f"Median:                     {observations.median():,.1f}")
    print(f"Minimum:                    {observations.min():,}")
    print(f"Maximum:                    {observations.max():,}")


if all_timestamps:
    timestamps = pd.Series(pd.to_datetime(all_timestamps))

    print("\nDATE RANGE")
    print("-" * 40)
    print(f"Earliest observation:       {timestamps.min()}")
    print(f"Latest observation:         {timestamps.max()}")


if all_prices:
    prices = pd.Series(all_prices)

    print("\nPRICE DISTRIBUTION")
    print("-" * 40)
    print(f"Minimum price:              ${prices.min():,.4f}")
    print(f"Median price:               ${prices.median():,.4f}")
    print(f"Mean price:                 ${prices.mean():,.4f}")
    print(f"95th percentile:            ${prices.quantile(0.95):,.4f}")
    print(f"99th percentile:            ${prices.quantile(0.99):,.4f}")
    print(f"Maximum price:              ${prices.max():,.4f}")


if all_volumes:
    volumes = pd.Series(all_volumes)

    print("\nSALES / OBSERVATION QUANTITY")
    print("-" * 40)
    print(f"Minimum quantity:           {volumes.min():,.0f}")
    print(f"Median quantity:            {volumes.median():,.0f}")
    print(f"Mean quantity:              {volumes.mean():,.2f}")
    print(f"95th percentile:            {volumes.quantile(0.95):,.0f}")
    print(f"Maximum quantity:            {volumes.max():,.0f}")


print("\n" + "=" * 60)
print("VALIDATION COMPLETE")
print("=" * 60)

print("\nINVALID HISTORY DETAILS")
print("-" * 40)

for filename, error in invalid_histories[:50]:
    print(f"{filename}")
    print(f"  {error}")