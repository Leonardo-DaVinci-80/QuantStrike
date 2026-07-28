from backend.repositories.skin_repository import SkinRepository

repo = SkinRepository(
    index_file=r"C:\Users\siddh\.cache\kagglehub\datasets\leawind\steam-market-price-dataset-csgo\versions\2\dataset_publish\item_index.csv",
    items_directory=r"C:\Users\siddh\.cache\kagglehub\datasets\leawind\steam-market-price-dataset-csgo\versions\2\dataset_publish\items",
)

skin = repo.find("AK-47 | The Empress (Field-Tested)")
print(skin)