from __future__ import annotations

from core.decision.models import DecisionResult

from llm.factory import LLMFactory
from llm.reasoning_result import ReasoningResult
from llm.reasoning_service import ReasoningService


class ReasoningEngine:
    """
    PredatorAI AI Reasoning Layer.

    Enhances DecisionResults with an external
    language model while keeping the original
    decision completely untouched.
    """

    def __init__(
        self,
        provider: str = "local",
    ) -> None:

        self.provider = LLMFactory.create(
            provider
        )

        self.service = ReasoningService(
            self.provider
        )

    def enhance(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        response = self.service.generate(
            decision
        )

        return ReasoningResult(
            summary=response,
            technical_analysis=response,
            executive_summary=response,
            remediation_strategy=response,
            confidence=decision.confidence.score,
        )

    def enhance_many(
        self,
        decisions: list[DecisionResult],
    ) -> list[ReasoningResult]:

        results: list[ReasoningResult] = []

        for decision in decisions:

            results.append(
                self.enhance(
                    decision
                )
            )

        return results
    