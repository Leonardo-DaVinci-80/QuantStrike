from backend.analytics.market_overview import MarketOverviewAnalyzer
from backend.repositories.skin_repository import SkinRepository


repository = SkinRepository(
    index_file="data/demo/item_index.csv",
    items_directory="data/demo/items",
)
analyzer = MarketOverviewAnalyzer(repository)

# PRICE MATRIX
prices = analyzer.build_daily_price_matrix()

print("\nPRICE MATRIX")
print("-------------------------")
print("Shape:", prices.shape)
print(prices.head())

# RETURNS
returns = analyzer.build_daily_returns()

print("\nRETURN COVERAGE")
print("-------------------------")

coverage = returns.notna().sum(axis=1)

print("First non-zero coverage:")
print(coverage[coverage > 0].head())

print("\nHighest coverage:")
print(coverage.max())

print("\nCoverage around QSI start:")

print(
    coverage.loc[
        "2020-01-01":
    ].sort_values(
        ascending=False
    ).head(20)
)

print("\nRETURNS")
print("-------------------------")
print(returns.head())

# BREADTH
breadth = analyzer.market_breadth()

print("\nBREADTH")
print("-------------------------")
print(breadth.tail())

# QSI
qsi = analyzer.calculate_qsi()

print("\nQSI DIAGNOSTICS")
print("-------------------------")
print("Start:", qsi.index[0])
print("End:", qsi.index[-1])
print("Days:", len(qsi))
print("Min:", qsi.min())
print("Max:", qsi.max())
print("Final:", qsi.iloc[-1])

# MARKET RETURNS
print("\nMARKET RETURN DIAGNOSTICS")
print("-------------------------")

market_returns = analyzer.market_returns()

print("Mean:", market_returns.mean())
print("Median:", market_returns.median())
print("P01:", market_returns.quantile(0.01))
print("P99:", market_returns.quantile(0.99))