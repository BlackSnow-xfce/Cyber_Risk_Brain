from __future__ import annotations

from core.decision.models import DecisionResult


class ReasoningService:
    """
    Thin wrapper around the configured LLM.

    Every Reviewer and Challenger uses
    this service.
    """

    def __init__(
        self,
        provider,
    ) -> None:

        self.provider = provider

    def review(
        self,
        decision: DecisionResult,
        prompt: str,
    ) -> str:

        return self.provider.generate(

            prompt=prompt,

            context=decision.to_dict(),

        )

    def ask(
        self,
        prompt: str,
    ) -> str:

        return self.provider.generate(

            prompt=prompt,

        )
    