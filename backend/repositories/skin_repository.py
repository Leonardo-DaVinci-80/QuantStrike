import pandas as pd
from pathlib import Path
import re
from urllib.parse import unquote

from backend.models.skin import Skin
import streamlit as st

@st.cache_data(
    show_spinner=False,
    max_entries=5000,
    ttl=60 * 60 * 24
)
def get_latest_price(filepath: str) -> float:
    """
    Return the latest valid price from a skin CSV.

    Cached independently so searching for skins does not
    repeatedly read the same historical CSV files.
    """

    filepath = Path(filepath)

    if not filepath.exists():
        return 0.0

    try:
        df = pd.read_csv(
            filepath,
            usecols=[
                "price",
                "unix timestamp"
            ]
        )

        df["price"] = pd.to_numeric(
            df["price"],
            errors="coerce"
        )

        df["unix timestamp"] = pd.to_numeric(
            df["unix timestamp"],
            errors="coerce"
        )

        df = df.dropna(
            subset=[
                "price",
                "unix timestamp"
            ]
        )

        df = df[
            df["price"] >= 0.001
        ]

        if df.empty:
            return 0.0

        latest_index = df["unix timestamp"].idxmax()

        return float(
            df.loc[latest_index, "price"]
        )

    except Exception:
        return 0.0

class SkinRepository:

    def __init__(self, index_file: str, items_directory: str):
        self.items_directory = items_directory

        self.index = pd.read_csv(index_file)

        # New Kaggle dataset:
        # "URL encoded name","decoded name"
        self.index["name"] = self.index["decoded name"]
        self.index["file_name"] = self.index["URL encoded name"].apply(unquote) + ".csv"
        self.index["base_name"] = (
        self.index["name"]
        .str.replace(
            "StatTrak™ ",
            "",
            regex=False
        )
        .str.replace(
            "Souvenir ",
            "",
            regex=False
        )
        .str.rsplit(
            " (",
            n=1
        )
        .str[0]
    )

    def search(self, query: str):
        results = self.index[
            self.index["name"].str.contains(
                query,
                case=False,
                na=False,
                regex=False
            )
        ]

        skins = []

        for _, row in results.iterrows():
            attributes = self.parse_name(row["name"])

            skins.append(
                Skin(
                    id=row["file_name"],
                    name=row["name"],
                    weapon=attributes["weapon"],
                    finish=attributes["finish"],
                    condition=attributes["condition"],
                    stattrak=attributes["stattrak"],
                    souvenir=attributes["souvenir"],
                    history_file=str(
                        Path(self.items_directory) / row["file_name"]
                    )
                )
            )

        return skins, results

    def search_base_skins(self, query: str):
        def normalize(text):
            return (
                str(text)
                .lower()
                .replace("-", "")
                .replace(" ", "")
                .replace("★", "")
            )

        query = re.sub(r"\s*\([^)]*\)\s*$", "", query.strip())
        query = normalize(query)

        base_names = set()

        for name in self.index["name"]:
            cleaned = (
                name
                .replace("StatTrak™ ", "")
                .replace("Souvenir ", "")
            )

            base = cleaned.rsplit(" (", 1)[0]

            if query in normalize(base):
                base_names.add(base)

        base_prices = []

        for base_name in base_names:
            matching_rows = self.index[
                self.index["name"].apply(
                    lambda name: (
                        name
                        .replace("StatTrak™ ", "")
                        .replace("Souvenir ", "")
                        .rsplit(" (", 1)[0]
                    ) == base_name
                )
            ]

            latest_price = 0.0

            for _, row in matching_rows.iterrows():
                filepath = (
                    Path(self.items_directory)
                    / row["file_name"]
                )

                price = get_latest_price(str(filepath))

                latest_price = max(
                    latest_price,
                    price
                )

            base_prices.append(
                (base_name, latest_price)
            )

        base_prices.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return [
            name
            for name, _ in base_prices
        ]

    def find(self, query: str) -> Skin:
        results = self.index[
            self.index["name"].str.lower() == query.lower()
        ]

        if results.empty:
            raise ValueError(f"No skin found: {query}")

        row = results.iloc[0]
        attributes = self.parse_name(row["name"])

        return Skin(
            id=row["file_name"],
            name=row["name"],
            weapon=attributes["weapon"],
            finish=attributes["finish"],
            condition=attributes["condition"],
            stattrak=attributes["stattrak"],
            souvenir=attributes["souvenir"],
            history_file=str(
                Path(self.items_directory) / row["file_name"]
            )
        )

    @staticmethod
    def parse_name(name: str):
        """
        Parse a Steam market item name into structured attributes.
        """

        stattrak = name.startswith("StatTrak™")
        souvenir = name.startswith("Souvenir")

        cleaned = (
            name
            .replace("StatTrak™ ", "")
            .replace("Souvenir ", "")
        )

        if " | " not in cleaned:
            # Vanilla knife/glove/agent/etc.
            return {
                "weapon": cleaned,
                "finish": None,
                "condition": "Vanilla",
                "stattrak": stattrak,
                "souvenir": souvenir,
            }

        weapon, remainder = cleaned.split(" | ", 1)

        if " (" not in remainder:
            # Has a finish but no wear condition
            finish = remainder
            condition = "Vanilla"
        else:
            finish, condition = remainder.rsplit(" (", 1)
            condition = condition.rstrip(")")

        return {
            "weapon": weapon,
            "finish": finish,
            "condition": condition,
            "stattrak": stattrak,
            "souvenir": souvenir,
        }

    def get_variants(self, base_name: str):
        names = self.index["name"]

        cleaned = (
            names
            .str.replace("StatTrak™ ", "", regex=False)
            .str.replace("Souvenir ", "", regex=False)
            .str.rsplit(" (", n=1).str[0]
        )

        matching_rows = self.index[cleaned == base_name]

        variants = []

        for _, row in matching_rows.iterrows():
            attributes = self.parse_name(row["name"])

            variants.append(
                {
                    "name": row["name"],
                    "stattrak": attributes["stattrak"],
                    "souvenir": attributes["souvenir"],
                    "condition": attributes["condition"],
                }
            )

        return variants

    def load_history(self, filepath):
        from backend.collectors.csv_collector import CSVCollector
        return CSVCollector.load_history(str(filepath))