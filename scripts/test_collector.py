from backend.collectors.csv_collector import CSVCollector
from backend.analytics.market_metrics import MarketMetrics


history = CSVCollector.load_history(
    r"C:\Users\siddh\.cache\kagglehub\datasets\leawind\steam-market-price-dataset-csgo\versions\2\dataset_publish\items\0.csv"
)
print("Number of prices:", len(history))
print("First point:")
print(history[0])
metrics = MarketMetrics(history)

print()
print("Current price:", metrics.current_price)
print("Daily change:", metrics.daily_change)
print("Daily change %:", metrics.daily_change_percent)
print("All time high:", metrics.all_time_high)
print("All time low:", metrics.all_time_low)