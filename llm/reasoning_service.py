from __future__ import annotations

from llm.llm_provider import LLMProvider


class ReasoningService:
    """
    Executes prompts against the configured LLM.

    The service does not know anything about
    PredatorAI decisions.
    """

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:

        self.provider = provider

    def generate_prompt(
        self,
        prompt: str,
    ) -> str:

        return self.provider.generate(
            prompt
        )
    