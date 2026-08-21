import base64
import pandas as pd
from pathlib import Path
from backend.models.skin import Skin
import re


class SkinRepository:

    def __init__(self, index_file: str, items_directory: str):
        self.items_directory = items_directory

        self.index = pd.read_csv(index_file)

        self.index["name"] = (
            self.index["item_hash_name_base64"]
            .apply(self.decode_name)
        )


    @staticmethod
    def decode_name(value: str) -> str:
        decoded = base64.b64decode(value)

        return decoded.decode("utf-8")


    def search(self, query: str):
        results = self.index[
            self.index["name"]
            .str.contains(
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

                    history_file=(
                        f"{self.items_directory}/"
                        f"{row['file_name']}"
                    )
                )
            )

        return skins, results

    def search_base_skins(self, query: str):

        def normalize(text):
            return (
                text
                .lower()
                .replace("-", "")
                .replace(" ", "")
                .replace("★", "")
            )

        # Strip a trailing wear condition if the user pasted a full name
        wear_conditions = {
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred",
        }

        query = query.strip()

        for condition in wear_conditions:
            suffix = f" ({condition})"

            if query.lower().endswith(suffix.lower()):
                query = query[:-len(suffix)]
                break

        query = normalize(query)

        names = []

        for name in self.index["name"]:

            attributes = self.parse_name(name)

            cleaned = (
                name
                .replace("StatTrak™ ", "")
                .replace("Souvenir ", "")
            )

            # Remove ONLY actual wear conditions
            if attributes["condition"] in wear_conditions:
                base = cleaned.rsplit(" (", 1)[0]
            else:
                base = cleaned

            if query in normalize(base):

                if base not in names:
                    names.append(base)

        return names

    def find(self, query: str) -> Skin:
        results = self.index[
            self.index["name"]
            .str.lower() == query.lower()
        ]

        if results.empty:
            raise ValueError(
                f"No skin found: {query}"
            )

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

        wear_conditions = {
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred",
        }

        if " | " not in cleaned:
            return {
                "weapon": cleaned,
                "finish": None,
                "condition": "Vanilla",
                "stattrak": stattrak,
                "souvenir": souvenir,
            }

        weapon, remainder = cleaned.split(" | ", 1)

        # Only interpret parentheses as wear conditions
        # when they contain an actual CS2 wear condition.
        condition = "Vanilla"
        finish = remainder

        if remainder.endswith(")"):
            match = re.search(r"\(([^()]*)\)$", remainder)

            if match:
                possible_condition = match.group(1)

                if possible_condition in wear_conditions:
                    condition = possible_condition
                    finish = remainder[:match.start()].rstrip()

        return {
            "weapon": weapon,
            "finish": finish,
            "condition": condition,
            "stattrak": stattrak,
            "souvenir": souvenir,
        }

    def get_variants(self, base_name: str):

        variants = []

        wear_conditions = {
            "Factory New",
            "Minimal Wear",
            "Field-Tested",
            "Well-Worn",
            "Battle-Scarred",
        }

        for _, row in self.index.iterrows():

            name = row["name"]

            attributes = self.parse_name(name)

            cleaned = (
                name
                .replace("StatTrak™ ", "")
                .replace("Souvenir ", "")
            )

            # Remove wear condition only.
            if attributes["condition"] in wear_conditions:
                skin_base = cleaned.rsplit(" (", 1)[0]
            else:
                skin_base = cleaned

            if skin_base == base_name:

                variants.append(
                    {
                        "name": name,
                        "stattrak": attributes["stattrak"],
                        "souvenir": attributes["souvenir"],
                        "condition": attributes["condition"],
                    }
                )

        return variants