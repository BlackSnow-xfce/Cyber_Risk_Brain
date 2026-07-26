from __future__ import annotations

from llm.llm_provider import LLMProvider


class LocalProvider(LLMProvider):
    """
    Placeholder implementation for a local LLM
    (e.g. Ollama or LM Studio).
    """

    def __init__(self) -> None:
        self.model = "local"

    def generate(
        self,
        prompt: str,
    ) -> str:
        raise NotImplementedError(
            "LocalProvider has not been implemented yet."
        )
    