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
# Load data
# ---------------------------------------------------------

collector = MarketCSGOCollector()

history_index = collector.load_history_index()

repository = SkinRepository(
    index_file=INDEX_FILE,
    items_directory=ITEMS_DIRECTORY
)

tracked_names = set(
    repository.index["name"]
)


# ---------------------------------------------------------
# Coverage
# ---------------------------------------------------------

history_names = set(
    history_index.keys()
)

matched = tracked_names.intersection(
    history_names
)

missing = tracked_names - history_names


coverage = (
    len(matched)
    / len(tracked_names)
    * 100
)


# ---------------------------------------------------------
# Results
# ---------------------------------------------------------

print(
    f"Market.CSGO historical items: "
    f"{len(history_names):,}"
)

print(
    f"QuantStrike assets: "
    f"{len(tracked_names):,}"
)

print()

print("MARKET.CSGO HISTORY COVERAGE")
print("-------------------------")

print(
    f"Tracked assets:       {len(tracked_names):,}"
)

print(
    f"Historical matches:   {len(matched):,}"
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

for name in sorted(missing)[:50]:
    print(name)