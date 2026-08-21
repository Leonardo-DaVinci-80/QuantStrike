from backend.collectors.market_csgo_collector import (
    MarketCSGOCollector
)

from backend.repositories.skin_repository import SkinRepository


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

INDEX_FILE = "data/demo/item_index.csv"
ITEMS_DIRECTORY = "data/demo/items"


# ---------------------------------------------------------
# Load Market.CSGO
# ---------------------------------------------------------

collector = MarketCSGOCollector()

prices = collector.load_prices()

print(
    f"Market.CSGO prices: {len(prices):,}"
)


# ---------------------------------------------------------
# Load QuantStrike universe
# ---------------------------------------------------------

repository = SkinRepository(
    index_file=INDEX_FILE,
    items_directory=ITEMS_DIRECTORY
)

tracked_names = set(
    repository.index["name"]
)

print(
    f"QuantStrike assets: {len(tracked_names):,}"
)


# ---------------------------------------------------------
# Match
# ---------------------------------------------------------

matched = tracked_names.intersection(
    prices.keys()
)

missing = tracked_names - prices.keys()


coverage = (
    len(matched)
    / len(tracked_names)
    * 100
)


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print()
print("MARKET.CSGO COVERAGE")
print("-------------------------")

print(
    f"Tracked assets:       {len(tracked_names):,}"
)

print(
    f"Market.CSGO matches:  {len(matched):,}"
)

print(
    f"Missing:              {len(missing):,}"
)

print(
    f"Coverage:             {coverage:.2f}%"
)


# ---------------------------------------------------------
# Missing examples
# ---------------------------------------------------------

print()
print("MISSING EXAMPLES")
print("-------------------------")

for name in sorted(missing)[:25]:
    print(name)