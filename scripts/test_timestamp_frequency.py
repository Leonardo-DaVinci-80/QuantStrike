from pathlib import Path
import pandas as pd

ITEMS_DIRECTORY = Path("data/raw/items")

files = list(ITEMS_DIRECTORY.glob("*.csv"))

print(f"Scanning {len(files):,} history files...\n")

frequency_counts = {}
sample_intervals = []

for i, filepath in enumerate(files, 1):

    try:
        df = pd.read_csv(filepath)

        if "unix timestamp" not in df.columns:
            continue

        timestamps = pd.to_datetime(
            df["unix timestamp"],
            unit="s",
            errors="coerce"
        ).dropna()

        if len(timestamps) < 2:
            continue

        intervals = timestamps.diff().dropna().dt.total_seconds() / 3600

        for interval in intervals:
            rounded = round(interval, 2)
            frequency_counts[rounded] = frequency_counts.get(rounded, 0) + 1

    except Exception:
        continue

    if i % 2000 == 0:
        print(f"Processed {i:,} / {len(files):,}")


print("\n" + "=" * 60)
print("TIMESTAMP FREQUENCY ANALYSIS")
print("=" * 60)

sorted_frequencies = sorted(
    frequency_counts.items(),
    key=lambda x: x[1],
    reverse=True
)

print("\nMost common observation intervals:")
print("-" * 40)

for interval, count in sorted_frequencies[:20]:
    print(f"{interval:8.2f} hours : {count:,} observations")


print("\nKey intervals:")
print("-" * 40)

targets = [1, 3, 6, 12, 24, 48, 72, 168]

for target in targets:
    closest = min(
        frequency_counts,
        key=lambda x: abs(x - target)
    )

    print(
        f"~{target:3}h: "
        f"{closest:8.2f}h "
        f"({frequency_counts[closest]:,} observations)"
    )

print("\n" + "=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)