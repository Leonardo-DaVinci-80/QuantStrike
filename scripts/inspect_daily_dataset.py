import pyarrow.parquet as pq #type:ignore
from pathlib import Path


path = Path("data/processed/daily_market_data.parquet")

table = pq.ParquetFile(path)

print("=" * 60)
print("DAILY DATASET INSPECTION")
print("=" * 60)

print("\nFile size:")
print(f"{path.stat().st_size / 1024**2:.2f} MB")

print("\nRows:")
print(f"{table.metadata.num_rows:,}")

print("\nColumns:")
for field in table.schema_arrow:
    print(f"  {field.name}: {field.type}")

print("\nRow groups:")
print(table.metadata.num_row_groups)

print("\nCompression:")
for i in range(table.metadata.num_row_groups):
    row_group = table.metadata.row_group(i)

    for j in range(row_group.num_columns):
        column = row_group.column(j)

        print(
            f"  {column.path_in_schema}: "
            f"{column.total_compressed_size / 1024**2:.2f} MB"
        )

    if i >= 4:
        print("  ...")
        break