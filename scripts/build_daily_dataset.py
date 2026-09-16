import time
from pathlib import Path

from backend.repositories.skin_repository import SkinRepository
from backend.analytics.daily_market_data import DailyMarketDataBuilder


def main():

    repo = SkinRepository(
        index_file="data/raw/name_conversion_table.csv",
        items_directory="data/raw/items",
    )

    builder = DailyMarketDataBuilder(repo)

    output_path = Path(
        "data/processed/daily_market_data.parquet"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    print("=" * 60)
    print("BUILDING DAILY MARKET DATASET")
    print("=" * 60)

    start = time.perf_counter()

    daily = builder.build_daily_dataset(
        max_assets=None,
        min_observations=30,
    )

    elapsed = time.perf_counter() - start

    daily.to_parquet(
        output_path,
        index=False,
        compression="snappy"
    )

    print("\n" + "=" * 60)
    print("BUILD COMPLETE")
    print("=" * 60)

    print(f"\nRows:       {len(daily):,}")
    print(f"Assets:     {daily['asset_id'].nunique():,}")
    print(f"Date range: {daily['date'].min()} → {daily['date'].max()}")
    print(f"File size:  {output_path.stat().st_size / 1024**2:.2f} MB")
    print(f"Build time: {elapsed:.2f} seconds")
    print(f"\nSaved to:   {output_path}")


if __name__ == "__main__":
    main()