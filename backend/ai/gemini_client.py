"""
Gemini API client for QuantStrike.

This module is responsible only for communicating with Gemini.
It should not contain QuantStrike market calculations.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from google import genai


# Load environment variables from .env
load_dotenv()


MODEL_NAME = "gemini-3.8-flash"


class GeminiClient:
    """
    Small wrapper around the Gemini Interactions API.

    Keeping Gemini behind this class means the rest of QuantStrike
    does not need to know anything about the Gemini SDK.
    """

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY was not found. "
                "Create a .env file and add your Gemini API key."
            )

        self.client = genai.Client(api_key=api_key)

    def generate(
        self,
        prompt: str,
        system_instruction: str | None = None,
    ) -> str:
        """
        Send a prompt to Gemini and return the generated text.
        """

        kwargs = {
            "model": MODEL_NAME,
            "input": prompt,
        }

        if system_instruction:
            kwargs["system_instruction"] = system_instruction

        interaction = self.client.interactions.create(**kwargs)

        output = interaction.output_text

        if not output:
            raise RuntimeError(
                "Gemini returned an empty response."
            )

        return output