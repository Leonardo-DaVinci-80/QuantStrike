import shutil
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
DEMO = ROOT / "data" / "demo"

DEMO.mkdir(parents=True, exist_ok=True)
(DEMO / "items").mkdir(exist_ok=True)

index = pd.read_csv(RAW / "item_index.csv")

# Decode names the same way SkinRepository does
import base64
def decode_name(value):
    return base64.b64decode(value).decode("utf-8")

index["name"] = index["item_hash_name_base64"].apply(decode_name)

KEYWORDS = [
    # AK-47
    "Redline",
    "Asiimov",
    "Fire Serpent",
    "Vulcan",
    "Bloodsport",
    "Fuel Injector",
    "Aquamarine Revenge",
    "Case Hardened",
    "Neon Rider",
    "Legion of Anubis",
    "Head Shot",

    # AWP
    "Dragon Lore",
    "Asiimov",
    "Hyper Beast",
    "Lightning Strike",
    "Containment Breach",
    "Graphite",
    "BOOM",
    "Oni Taiji",
    "Wildfire",

    # M4
    "Howl",
    "Printstream",
    "Neo-Noir",
    "Poseidon",
    "Golden Coil",
    "Chantico's Fire",
    "The Emperor",
    "Hellfire",
    "Cyrex",

    # USP / Glock / Deagle
    "Kill Confirmed",
    "Neo-Noir",
    "Bullet Queen",
    "Printstream",
    "Code Red",
    "Blaze",
    "Kumicho Dragon",
    "Cobalt Disruption",

    # Knives
    "Karambit",
    "Butterfly",
    "Bayonet",
    "M9 Bayonet",
    "Flip Knife",
    "Skeleton Knife",
    "Talon Knife",
    "Nomad Knife",
    "Stiletto Knife",
    "Huntsman Knife",
    "Falchion Knife",
    "Bowie Knife",
    "Classic Knife",
    "Paracord Knife",
    "Ursus Knife",
    "Navaja Knife",

    # Knife Finishes
    "Fade",
    "Doppler",
    "Gamma Doppler",
    "Marble Fade",
    "Tiger Tooth",
    "Slaughter",
    "Lore",
    "Crimson Web",
    "Autotronic",
    "Black Laminate",
    "Damascus Steel",

    # Gloves
    "Sport Gloves",
    "Driver Gloves",
    "Moto Gloves",
    "Specialist Gloves",
    "Hand Wraps",
    "Hydra Gloves",
    "Broken Fang Gloves",

    # Cases
    "Case",
    "Weapon Case",
    "Operation",

    # Stickers / Capsules
    "Sticker",
    "Capsule",

    # Misc
    "Hyper Beast",
    "Leet Museo",
    "Mecha Industries",
    "Desolate Space",
    "Whiteout"
]

mask = index["name"].str.contains("|".join(KEYWORDS), case=False, na=False)
subset = index[mask]

print(f"Selected {len(subset)} rows out of {len(index)}")

subset.to_csv(DEMO / "item_index.csv", index=False)

for _, row in subset.iterrows():
    src = RAW / "items" / row["file_name"]
    dst = DEMO / "items" / row["file_name"]
    if src.exists():
        shutil.copy(src, dst)

print("Demo dataset built at", DEMO)