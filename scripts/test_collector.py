from backend.collectors.csv_collector import CSVCollector

history = CSVCollector.load_history(
    r"data/raw/items/AK-47%20%7C%20Asiimov%20(Factory%20New).csv"
)

print("Number of observations:", len(history))

print("\nFirst point:")
print(history[0])

print("\nLast point:")
print(history[-1])

print("\nFirst 5 volumes:")
print([point.volume for point in history[:5]])