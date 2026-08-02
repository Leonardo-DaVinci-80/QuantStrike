import shutil
import kagglehub
from pathlib import Path

path = kagglehub.dataset_download("leawind/steam-market-price-dataset-csgo")
print("Downloaded to:", path)

dest = Path(__file__).parent.parent / "data" / "raw"
dest.mkdir(parents=True, exist_ok=True)
shutil.copytree(Path(path) / "dataset_publish", dest, dirs_exist_ok=True)
print("Copied to:", dest)