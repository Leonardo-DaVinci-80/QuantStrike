from pathlib import Path
import pyarrow as pa #type:ignore
import pyarrow.parquet as pq #type:ignore
import pyarrow.dataset as ds #type:ignore


SOURCE = Path("data/processed/daily_market_data.parquet")
OUTPUT = Path("data/processed/daily_market_data")


def main():
    print("=" * 60)
    print("PARTITIONING DAILY MARKET DATASET")
    print("=" * 60)

    if not SOURCE.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {SOURCE}"
        )

    if OUTPUT.exists():
        raise FileExistsError(
            f"Output already exists: {OUTPUT}\n"
            "Delete it manually if you want to rebuild it."
        )

    parquet_file = pq.ParquetFile(SOURCE)

    print(f"\nSource: {SOURCE}")
    print(f"Rows:   {parquet_file.metadata.num_rows:,}")
    print(f"Row groups: {parquet_file.metadata.num_row_groups}")

    columns = [
        "date",
        "asset_id",
        "price",
        "observation_count",
    ]

    # Get the schema for exactly the columns we're keeping.
    source_schema = parquet_file.schema_arrow
    schema = pa.schema([
        source_schema.field("date"),
        source_schema.field("asset_id"),
        source_schema.field("price"),
        source_schema.field("observation_count"),
    ])

    print("\nWriting partitioned dataset...")
    print("Partition: date")
    print("Columns:   date, asset_id, price, observation_count")

    batches = parquet_file.iter_batches(
        batch_size=250_000,
        columns=columns,
    )

    ds.write_dataset(
        data=batches,
        base_dir=str(OUTPUT),
        schema=schema,
        format="parquet",
        partitioning=["date"],
        partitioning_flavor="hive",
        existing_data_behavior="error",
        max_rows_per_file=250_000,
        max_rows_per_group=50_000,
        file_options=ds.ParquetFileFormat().make_write_options(
            compression="snappy"
        ),
    )

    print("\n" + "=" * 60)
    print("PARTITIONING COMPLETE")
    print("=" * 60)

    total_size = sum(
        p.stat().st_size
        for p in OUTPUT.rglob("*")
        if p.is_file()
    )

    partition_count = sum(
        1
        for p in OUTPUT.iterdir()
        if p.is_dir()
    )

    file_count = sum(
        1
        for p in OUTPUT.rglob("*.parquet")
    )

    print(f"\nPartitions: {partition_count:,}")
    print(f"Parquet files: {file_count:,}")
    print(f"Output size: {total_size / 1024**2:.2f} MB")
    print(f"\nSaved to: {OUTPUT}")


if __name__ == "__main__":
    main()