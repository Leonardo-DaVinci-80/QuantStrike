"""
QuantStrike AI market-context test.
"""

import pandas as pd

from backend.ai.market_ai import MarketAI


def main() -> None:
    print("=" * 70)
    print("QuantStrike AI Market Analysis Test")
    print("=" * 70)

    # Temporary fake QuantStrike data.

    # Later this will be replaced with the real output from
    # MarketAnalytics / market_repository.
    market_data = pd.DataFrame(
        [
            {
                "metric": "QSI",
                "value": 104.82,
                "change_24h": 1.42,
                "change_7d": 3.18,
            },
            {
                "metric": "Market Volume",
                "value": 1240000,
                "change_24h": 18.2,
                "change_7d": 11.4,
            },
            {
                "metric": "Advancing Assets",
                "value": 61.4,
                "change_24h": None,
                "change_7d": None,
            },
            {
                "metric": "Declining Assets",
                "value": 28.7,
                "change_24h": None,
                "change_7d": None,
            },
            {
                "metric": "Unchanged Assets",
                "value": 9.9,
                "change_24h": None,
                "change_7d": None,
            },
        ]
    )

    try:
        ai = MarketAI()

        print("\nAsking QuantStrike AI...\n")

        response = ai.ask_about_dataframe(
            question=(
                "Summarize the current market conditions. "
                "What does the combination of QSI performance, "
                "volume and market breadth indicate?"
            ),
            dataframe=market_data,
        )

        print("=" * 70)
        print("QUANTSTRIKE AI")
        print("=" * 70)
        print(response)
        print("=" * 70)

    except Exception as exc:
        print("\nFAILED:")
        print(type(exc).__name__)
        print(exc)


if __name__ == "__main__":
    main()

