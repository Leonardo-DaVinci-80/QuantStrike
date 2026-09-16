from backend.repositories.skin_repository import SkinRepository


repo = SkinRepository(
    index_file="data/raw/name_conversion_table.csv",
    items_directory="data/raw/items",
)

skin = repo.find("AK-47 | Asiimov (Factory New)")

print("Found:")
print(skin)

print("\nHistory file:")
print(skin.history_file)