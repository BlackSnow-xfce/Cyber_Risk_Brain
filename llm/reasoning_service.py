from __future__ import annotations

from core.decision.models import DecisionResult

from llm.llm_provider import LLMProvider
from llm.prompt_builder import PromptBuilder


class ReasoningService:
    """
    Executes LLM reasoning.
    """

    def __init__(
        self,
        provider: LLMProvider,
    ) -> None:

        self.provider = provider

        self.builder = PromptBuilder()

    def generate(
        self,
        decision: DecisionResult,
    ) -> str:

        prompt = self.builder.build(
            decision
        )

        return self.provider.generate(
            prompt
        )
    