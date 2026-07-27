from __future__ import annotations

import os

from core.llm.local_provider import LocalProvider
from core.llm.ollama_provider import OllamaProvider
from core.llm.openai_provider import OpenAIProvider


class LLMFactory:
    """
    Creates the configured LLM provider.
    """

    @staticmethod
    def create(
        provider: str | None = None,
    ):

        provider = (
            provider
            or os.getenv(
                "PREDATOR_LLM",
                "local",
            )
        ).lower()

        if provider == "ollama":

            return OllamaProvider()

        if provider == "openai":

            return OpenAIProvider()

        return LocalProvider()
    