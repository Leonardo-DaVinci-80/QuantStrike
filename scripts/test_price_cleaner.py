from backend.repositories.skin_repository import SkinRepository
from backend.collectors.csv_collector import CSVCollector
from backend.analytics.price_cleaner import PriceCleaner


def main():

    repo = SkinRepository(
        index_file="data/raw/name_conversion_table.csv",
        items_directory="data/raw/items",
    )

    skin_name = "AWP | Dragon Lore (Factory New)"

    print("=" * 60)
    print("TESTING PRICE CLEANER")
    print("=" * 60)

    skin = repo.find(skin_name)

    print(f"\nSkin: {skin.name}")
    print(f"File: {skin.history_file}")

    collector = CSVCollector()

    history = collector.load_history(
        skin.history_file
    )

    print(
        f"\nRaw observations: {len(history):,}"
    )

    cleaner = PriceCleaner(
        window=60,
        min_history=30,
        z_threshold=5.0,
    )

    result = cleaner.clean(history)

    print(
        f"Accepted:   {len(result.accepted):,}"
    )

    print(
        f"Suspicious: {len(result.suspicious):,}"
    )

    print(
        f"Rejected:   {len(result.rejected):,}"
    )

    print("\n" + "=" * 60)
    print("SUSPICIOUS OBSERVATIONS")
    print("=" * 60)

    for point in result.suspicious[:30]:
        print(
            f"{point.timestamp} | "
            f"${point.price:.4f} | "
            f"volume={point.volume}"
        )


if __name__ == "__main__":
    main()