from pathlib import Path
import pandas as pd


INDEX_FILE = Path("data/raw/name_conversion_table.csv")
ITEMS_DIRECTORY = Path("data/raw/items")


index = pd.read_csv(INDEX_FILE)

index["file_name"] = index["URL encoded name"] + ".csv"

missing_files = []

for filename in index["file_name"]:
    if not (ITEMS_DIRECTORY / filename).exists():
        missing_files.append(filename)


print("Items in conversion table:", len(index))
print("History files found:", len(index) - len(missing_files))
print("Missing history files:", len(missing_files))

if missing_files:
    print("\nFirst 20 missing files:")
    for filename in missing_files[:20]:
        print(filename)
else:
    print("\nEvery item has a corresponding history file.")