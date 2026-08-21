from typing import Dict
import requests
from datetime import datetime
from backend.models.price_point import PricePoint

class MarketCSGOCollector:

    BASE_URL = "https://market.csgo.com/api/v2"

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def load_prices(self) -> Dict[str, float]:

        url = f"{self.BASE_URL}/prices/USD.json"

        response = requests.get(
            url,
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):
            raise ValueError(
                "Market.CSGO API returned an unsuccessful response."
            )

        prices = {}

        for item in data.get("items", []):
            try:
                name = item["market_hash_name"]
                price = float(item["price"])

                if price <= 0:
                    continue

                prices[name] = price

            except (
                KeyError,
                TypeError,
                ValueError
            ):
                continue

        if not prices:
            raise ValueError(
                "Market.CSGO returned no valid prices."
            )

        return prices

    def load_history_index(self) -> Dict[str, int]:
        """
        Load the Market.CSGO historical sales index.

        Returns:
            market_hash_name -> history ID
        """

        url = f"{self.BASE_URL}/full-history/all.json"

        response = requests.get(
            url,
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()

        if "history" not in data:
            raise ValueError(
                "Market.CSGO returned no history index."
            )

        history = data["history"]

        if not isinstance(history, dict):
            raise ValueError(
                "Invalid Market.CSGO history index."
            )

        result = {}

        for name, item_id in history.items():

            try:
                result[name] = int(item_id)

            except (TypeError, ValueError):
                continue

        if not result:
            raise ValueError(
                "Market.CSGO history index is empty."
            )

        return result

    def load_item_history(
    self,
    history_id: int,
) -> list[PricePoint]:
        """
        Load detailed sales history for one Market.CSGO item.
        """

        url = (
            f"{self.BASE_URL}"
            f"/full-history/{history_id}.json"
        )

        response = requests.get(
            url,
            timeout=self.timeout
        )

        response.raise_for_status()

        data = response.json()

        if "data" not in data:
            raise ValueError(
                "Market.CSGO returned no item history."
            )

        history = data["data"].get("history", [])

        points = []

        for row in history:

            if len(row) < 3:
                continue

            try:
                timestamp = datetime.fromtimestamp(
                    row[0]
                )

                price = float(row[2])

            except (
                TypeError,
                ValueError,
                OverflowError
            ):
                continue

            if price <= 0:
                continue

            points.append(
                PricePoint(
                    timestamp=timestamp,
                    price=price,
                    volume=None,
                    source="market_csgo"
                )
            )

        return points