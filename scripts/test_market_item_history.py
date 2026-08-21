from backend.collectors.market_csgo_collector import (
    MarketCSGOCollector
)

from backend.repositories.skin_repository import SkinRepository


INDEX_FILE = "data/demo/item_index.csv"
ITEMS_DIRECTORY = "data/demo/items"


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


# ---------------------------------------------------------
# Load Market.CSGO history index
# ---------------------------------------------------------

collector = MarketCSGOCollector()

history_index = collector.load_history_index()


# ---------------------------------------------------------
# Select representative assets
# ---------------------------------------------------------

preferred = [
    "AK-47 | Redline (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "★ Karambit | Doppler (Factory New)",
    "★ Butterfly Knife | Fade (Factory New)",
    "Sport Gloves | Pandora's Box (Factory New)",
    "Glock-18 | Water Elemental (Field-Tested)",
    "Clutch Case",
    "10 Year Birthday Sticker Capsule",
]

test_items = [
    name
    for name in preferred
    if name in history_index
]

if len(test_items) < 5:

    test_items = list(
        tracked_names.intersection(
            history_index.keys()
        )
    )[:10]

# ---------------------------------------------------------
# Download histories
# ---------------------------------------------------------

print()
print("MARKET.CSGO ITEM HISTORY TEST")
print("=" * 60)


for name in test_items:

    history_id = history_index[name]

    print()
    print(name)
    print("-" * 60)

    try:

        history = collector.load_item_history(
            history_id
        )

        print(
            f"History ID: {history_id}"
        )

        print(
            f"Observations: {len(history):,}"
        )

        if not history:
            print("No usable observations.")
            continue

        print(
            f"First: "
            f"{history[0].timestamp} "
            f"${history[0].price:.2f}"
        )

        print(
            f"Last:  "
            f"{history[-1].timestamp} "
            f"${history[-1].price:.2f}"
        )

        print()
        print("Last 5 observations:")

        for point in history[-5:]:

            print(
                f"  {point.timestamp} "
                f"${point.price:.2f}"
            )

    except Exception as exc:

        print(
            f"ERROR: {exc}"
        )