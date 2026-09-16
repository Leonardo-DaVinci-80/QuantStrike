import time
import pyarrow.dataset as ds #type:ignore


DATASET = "data/processed/daily_market_data"


def main():
    print("=" * 60)
    print("TESTING PARTITIONED DAILY DATASET")
    print("=" * 60)

    dataset = ds.dataset(
        DATASET,
        format="parquet",
        partitioning="hive",
    )

    print("\nSchema:")
    print(dataset.schema)

    # Test a small recent date range.
    start = time.perf_counter()

    table = dataset.to_table(
        filter=(
            (ds.field("date") >= "2024-06-01")
            & (ds.field("date") <= "2024-06-15")
        ),
        columns=[
            "date",
            "asset_id",
            "price",
            "observation_count",
        ],
    )

    elapsed = time.perf_counter() - start

    print("\nRecent-date query:")
    print(f"Rows loaded: {table.num_rows:,}")
    print(f"Columns:     {table.num_columns}")
    print(f"Query time:  {elapsed:.3f} seconds")

    print("\nFirst 5 rows:")
    print(table.slice(0, 5).to_pandas())

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()