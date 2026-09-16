import time

from backend.repositories.skin_repository import SkinRepository
from backend.analytics.daily_market_data import DailyMarketDataBuilder


repo = SkinRepository(
    index_file="data/raw/name_conversion_table.csv",
    items_directory="data/raw/items",
)

builder = DailyMarketDataBuilder(repo)

start = time.perf_counter()

matrix = builder.build_daily_price_matrix(
    max_assets=None,
    min_observations=30,
)

elapsed = time.perf_counter() - start

print("\n" + "=" * 60)
print("DAILY MATRIX BENCHMARK")
print("=" * 60)

print(f"\nAssets included: {matrix.shape[1]:,}")
print(f"Days:            {matrix.shape[0]:,}")
print(f"Matrix shape:    {matrix.shape}")
print(f"Build time:      {elapsed:.2f} seconds")

print("\nDate range:")
print(matrix.index.min(), "→", matrix.index.max())

print("\nMissing values:")
print(f"{matrix.isna().sum().sum():,}")

print("\nMemory usage:")
print(f"{matrix.memory_usage(deep=True).sum() / 1024**2:.2f} MB")