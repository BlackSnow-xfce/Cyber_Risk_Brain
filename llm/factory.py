from __future__ import annotations

from llm.local_provider import LocalProvider
from llm.openai_provider import OpenAIProvider
from llm.llm_provider import LLMProvider


class LLMFactory:
    """
    Creates LLM providers.
    """

    @staticmethod
    def create(
        provider: str,
    ) -> LLMProvider:

        provider = provider.lower()

        if provider == "local":
            return LocalProvider()

        if provider == "openai":
            return OpenAIProvider()

        raise ValueError(
            f"Unknown provider: {provider}"
        )
    