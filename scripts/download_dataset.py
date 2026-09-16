import shutil
import kagglehub
from pathlib import Path


# Download the dataset
path = kagglehub.dataset_download(
    "kieranpoc/counter-strike-market-sale-data"
)

print("Downloaded to:", path)

# Destination inside QuantStrike
ROOT = Path(__file__).parent.parent
dest = ROOT / "data" / "raw"
dest.mkdir(parents=True, exist_ok=True)

# Copy the downloaded dataset directly into data/raw
source = Path(path)

for item in source.iterdir():
    target = dest / item.name

    if item.is_dir():
        shutil.copytree(item, target, dirs_exist_ok=True)
    else:
        shutil.copy2(item, target)

print("Copied to:", dest)