from pathlib import Path
import os

PROJECT_NAME = "QuantStrike"
VERSION = "1.5"

# Feature-module configuration. Paths resolve from the repository root, not
# the shell's current working directory. Override with environment variables.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.getenv("QUANTSTRIKE_DB", str(PROJECT_ROOT / "data" / "quantstrike_app.sqlite3")))
HISTORY_PATH = Path(os.getenv("QUANTSTRIKE_HISTORY_PATH", os.getenv("QUANTSTRIKE_HISTORICAL_FILE", str(PROJECT_ROOT / "data" / "processed" / "historical_prices.parquet"))))
HISTORY_TIMESTAMP = os.getenv("QUANTSTRIKE_HISTORY_TIMESTAMP", "timestamp")
HISTORY_ASSET = os.getenv("QUANTSTRIKE_HISTORY_ASSET", "skin_id")
HISTORY_PRICE = os.getenv("QUANTSTRIKE_HISTORY_PRICE", "price")
HISTORY_VOLUME = os.getenv("QUANTSTRIKE_HISTORY_VOLUME", "volume")
HISTORY_TIMESTAMP_FORMAT = os.getenv("QUANTSTRIKE_HISTORY_TIMESTAMP_FORMAT", "unix_seconds")
