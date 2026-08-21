from backend.analytics.market_overview import MarketOverviewAnalyzer
from backend.repositories.skin_repository import SkinRepository


repository = SkinRepository(
    index_file="data/demo/item_index.csv",
    items_directory="data/demo/items",
)

analyzer = MarketOverviewAnalyzer(repository)

summary = analyzer.dataset_summary()

for key, value in summary.items():
    print(f"{key}: {value}")