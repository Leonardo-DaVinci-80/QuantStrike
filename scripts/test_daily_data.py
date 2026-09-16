from backend.repositories.skin_repository import SkinRepository
from backend.analytics.daily_market_data import DailyMarketDataBuilder


repo = SkinRepository(
    index_file="data/raw/name_conversion_table.csv",
    items_directory="data/raw/items",
)

builder = DailyMarketDataBuilder(repo)

skin = repo.find("AK-47 | Asiimov (Factory New)")

history = repo.load_history(skin.history_file)

daily = builder.build_daily_price(history)

print("Native observations:", len(history))
print("Daily observations:", len(daily))

print("\nFirst 10 daily prices:")
print(daily.head(10))

print("\nLast 10 daily prices:")
print(daily.tail(10))

print("\nDate range:")
print(daily.index.min(), "→", daily.index.max())