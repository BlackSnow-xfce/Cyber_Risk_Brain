from __future__ import annotations

from llm.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """
    Placeholder implementation for an OpenAI backend.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-5.5",
    ) -> None:

        self.api_key = api_key
        self.model = model

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise NotImplementedError(
            "OpenAIProvider has not been implemented yet."
        )