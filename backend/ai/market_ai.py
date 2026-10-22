"""
QuantStrike market AI.

Converts small QuantStrike analytical results into context
that can be supplied to Gemini.
"""

from __future__ import annotations

import pandas as pd

from .gemini_client import GeminiClient
from .prompts import (
    MARKET_SYSTEM_INSTRUCTION,
    build_market_prompt,
)


class MarketAI:
    """
    AI interface for QuantStrike market analysis.
    """

    def __init__(self) -> None:
        self.gemini = GeminiClient()

    @staticmethod
    def dataframe_to_context(
        df: pd.DataFrame,
        max_rows: int = 50,
    ) -> str:
        """
        Convert a small DataFrame into compact text.

        We deliberately limit the amount of data sent to Gemini.
        """

        if df is None or df.empty:
            return "No data is currently available."

        data = df.head(max_rows).copy()

        return data.to_string(
            index=False,
            max_rows=max_rows,
        )

    def ask(
        self,
        question: str,
        market_context: str,
    ) -> str:
        """
        Ask Gemini a question using supplied QuantStrike data.
        """

        prompt = build_market_prompt(
            question=question,
            market_context=market_context,
        )

        return self.gemini.generate(
            prompt=prompt,
            system_instruction=MARKET_SYSTEM_INSTRUCTION,
        )

    def ask_about_dataframe(
        self,
        question: str,
        dataframe: pd.DataFrame,
        max_rows: int = 50,
    ) -> str:
        """
        Ask Gemini about a QuantStrike DataFrame.

        Only a small subset of the DataFrame is sent.
        """

        context = self.dataframe_to_context(
            dataframe,
            max_rows=max_rows,
        )

        return self.ask(
            question=question,
            market_context=context,
        )