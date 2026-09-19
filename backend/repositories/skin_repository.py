from pathlib import Path
import re
from urllib.parse import unquote

import pandas as pd
import streamlit as st

from backend.models.skin import Skin


class SkinRepository:
    """
    Repository backed by the processed skin metadata Parquet file.

    The application no longer needs to scan the raw historical CSVs
    when searching for skins or retrieving their latest prices.
    """

    def __init__(
        self,
        metadata_file: str,
        items_directory: str | None = None,
    ):
        self.metadata_file = Path(metadata_file)
        self.items_directory = (
            Path(items_directory) if items_directory else None
        )

        if not self.metadata_file.exists():
            raise FileNotFoundError(
                f"Skin metadata file not found: {self.metadata_file}"
            )

        self.index = self._load_metadata()

    @staticmethod
    @st.cache_data(show_spinner=False, ttl=60 * 60 * 24)
    def _read_metadata(metadata_file: str) -> pd.DataFrame:
        df = pd.read_parquet(
            metadata_file,
            engine="pyarrow",
        )

        required_columns = {
            "file_name",
            "name",
            "base_name",
            "weapon",
            "finish",
            "condition",
            "stattrak",
            "souvenir",
            "skin_id",
            "latest_price",
            "latest_timestamp",
        }

        missing = required_columns - set(df.columns)

        if missing:
            raise ValueError(
                f"Skin metadata is missing columns: {sorted(missing)}"
            )

        return df

    def _load_metadata(self) -> pd.DataFrame:
        return self._read_metadata(str(self.metadata_file))

    @staticmethod
    def _normalise(value: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    @staticmethod
    def _display_name(value: str) -> str:
        value = unquote(str(value))

        if value.lower().endswith(".csv"):
            value = value[:-4]

        return value

    @staticmethod
    def _parse_name(name: str) -> dict:
        """
        Parse a CS2 item name into its component fields.

        Supports:
        - Normal skins
        - StatTrak™ skins
        - Souvenir skins
        - Vanilla items
        """

        original = name.strip()

        stattrak = original.startswith("StatTrak™ ")
        souvenir = original.startswith("Souvenir ")

        if stattrak:
            clean_name = original[len("StatTrak™ "):]
        elif souvenir:
            clean_name = original[len("Souvenir "):]
        else:
            clean_name = original

        # Extract wear condition from the end of the name.
        condition_match = re.search(
            r"\(([^()]*)\)$",
            clean_name,
        )

        if condition_match:
            condition = condition_match.group(1)
            item_name = clean_name[:condition_match.start()].strip()
        else:
            condition = "Vanilla"
            item_name = clean_name

        # Vanilla items such as agents/cases/etc.
        if " | " not in item_name:
            return {
                "weapon": item_name,
                "finish": item_name,
                "condition": condition,
                "stattrak": stattrak,
                "souvenir": souvenir,
            }

        weapon, finish = item_name.split(" | ", 1)

        return {
            "weapon": weapon.strip(),
            "finish": finish.strip(),
            "condition": condition,
            "stattrak": stattrak,
            "souvenir": souvenir,
        }

    def _skin_from_row(self, row: pd.Series) -> Skin:
        return Skin(
            id=str(row["skin_id"]),
            name=self._display_name(row["name"]),
            weapon=self._display_name(row["weapon"]),
            finish=self._display_name(row["finish"]),
            condition=str(row["condition"]),
            stattrak=bool(row["stattrak"]),
            souvenir=bool(row["souvenir"]),
            history_file=str(row["file_name"]),
        )

    def search(self, query: str, limit: int = 50) -> list[Skin]:
        """
        Search all indexed items by name.
        """

        query = self._normalise(query)

        if not query:
            return []

        names = self.index["name"].astype(str)

        mask = names.str.lower().str.contains(
            query,
            regex=False,
            na=False,
        )

        results = self.index.loc[mask].copy()

        if results.empty:
            return []

        # Exact matches first, followed by names beginning with
        # the query, followed by general substring matches.
        results["_exact"] = (
            results["name"].str.lower() == query
        )

        results["_prefix"] = (
            results["name"].str.lower().str.startswith(query)
        )

        results = results.sort_values(
            by=["_exact", "_prefix", "latest_price"],
            ascending=[False, False, False],
        )

        return [
            self._skin_from_row(row)
            for _, row in results.head(limit).iterrows()
        ]

    def find(self, query: str) -> Skin | None:
        """
        Find an exact skin/item name.

        The query may be human-readable, while the metadata index
        may contain URL-encoded names.
        """

        query_normalised = self._normalise(
            self._display_name(query)
        )

        if not query_normalised:
            return None

        names = (
            self.index["name"]
            .astype(str)
            .map(self._display_name)
        )

        matches = self.index.loc[
            names.str.lower() == query_normalised
        ]

        if matches.empty:
            return None

        return self._skin_from_row(matches.iloc[0])

    def search_base_skins(
        self,
        query: str,
        limit: int = 50,
    ) -> list[Skin]:
        """
        Search for base skin/item names.

        Results represent the underlying item without:
        - StatTrak™
        - Souvenir
        - wear condition
        """

        query = self._normalise(query)

        if not query:
            return []

        # Use the already-normalised base_name column.
        base_names = (
            self.index["base_name"]
            .astype(str)
            .map(self._display_name)
        )

        mask = (
            base_names
            .str.lower()
            .str.contains(
                query,
                regex=False,
                na=False,
            )
        )

        results = self.index.loc[mask].copy()

        if results.empty:
            return []

        results["_display_base_name"] = results["base_name"].map(
            self._display_name
        )

        # Group all variants belonging to the same base item.
        grouped = (
            results.groupby(
                "_display_base_name",
                as_index=False,
            )
            .agg(
                latest_price=("latest_price", "max"),
            )
        )

        grouped["_exact"] = (
            grouped["_display_base_name"]
            .str.lower()
            .eq(query)
        )

        grouped["_prefix"] = (
            grouped["_display_base_name"]
            .str.lower()
            .str.startswith(query)
        )

        grouped = grouped.sort_values(
            by=[
                "_exact",
                "_prefix",
                "latest_price",
            ],
            ascending=[
                False,
                False,
                False,
            ],
        )

        selected = grouped.head(limit)

        # Find a representative row for each base name.
        representative = (
            results[
                results["_display_base_name"].isin(
                    selected["_display_base_name"]
                )
            ]
            .sort_values(
                [
                    "_display_base_name",
                    "latest_price",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .drop_duplicates(
                "_display_base_name"
            )
        )

        # Preserve ranking.
        representative = (
            selected[["_display_base_name"]]
            .merge(
                representative,
                on="_display_base_name",
                how="left",
            )
        )

        skins = []

        for _, row in representative.iterrows():
            skins.append(
                Skin(
                    id=str(row["skin_id"]),
                    name=str(row["_display_base_name"]),
                    weapon=str(row["weapon"]),
                    finish=str(row["finish"]),
                    condition="",
                    stattrak=False,
                    souvenir=False,
                    history_file=str(row["file_name"]),
                )
            )

        return skins

    def get_variants(self, skin: Skin | str) -> list[dict]:
        """
        Return all variants belonging to a base skin.

        Accepts either:
        - a Skin returned by search_base_skins()
        - a human-readable base-name string
        """

        if isinstance(skin, Skin):
            base_name = skin.name
        else:
            base_name = str(skin)

        base_name = self._normalise(
            self._display_name(base_name)
        )

        stored_base_names = (
            self.index["base_name"]
            .astype(str)
            .map(self._display_name)
        )

        mask = (
            stored_base_names
            .str.lower()
            .eq(base_name)
        )

        variants = self.index.loc[mask].copy()

        if variants.empty:
            return []

        variants["_display_name"] = variants["name"].map(
            self._display_name
        )

        variants = variants.sort_values(
            by=[
                "stattrak",
                "souvenir",
                "condition",
            ],
            ascending=[
                True,
                True,
                True,
            ],
        )

        return [
            {
                "name": str(row["_display_name"]),
                "skin_id": str(row["skin_id"]),
                "condition": str(row["condition"]),
                "stattrak": bool(row["stattrak"]),
                "souvenir": bool(row["souvenir"]),
                "latest_price": (
                    float(row["latest_price"])
                    if pd.notna(row["latest_price"])
                    else None
                ),
            }
            for _, row in variants.iterrows()
        ]

    def get_base_name(name: str) -> str:
        """
        Remove StatTrak™ / Souvenir prefixes and wear condition.
        """

        name = name.strip()

        if name.startswith("★ StatTrak™ "):
            name = name[len("★ StatTrak™ "):]

        elif name.startswith("StatTrak™ "):
            name = name[len("StatTrak™ "):]

        elif name.startswith("Souvenir "):
            name = name[len("Souvenir "):]

        name = re.sub(
            r"\s+\([^()]*\)$",
            "",
            name,
        )

        return name.strip()

    def get_by_id(self, skin_id: str) -> Skin | None:
        """
        Retrieve a skin directly by its unique skin ID.
        """
        matches = self.index.loc[
            self.index["skin_id"].astype(str) == str(skin_id)
        ]

        if matches.empty:
            return None

        return self._skin_from_row(matches.iloc[0])