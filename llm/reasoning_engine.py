from __future__ import annotations

from core.decision.models import DecisionResult

from llm.challenger import Challenger
from llm.consensus import Consensus
from llm.factory import LLMFactory
from llm.reasoning_result import ReasoningResult
from llm.reasoning_service import ReasoningService
from llm.reviewer import Reviewer


class ReasoningEngine:
    """
    PredatorAI AI Reasoning Orchestrator.

    Workflow

    Decision
        ↓
    Reviewer
        ↓
    Challenger
        ↓
    Consensus
        ↓
    Final ReasoningResult
    """

    def __init__(
        self,
        provider: str = "local",
    ) -> None:

        llm_provider = LLMFactory.create(
            provider
        )

        service = ReasoningService(
            llm_provider
        )

        self.reviewer = Reviewer(
            service
        )

        self.challenger = Challenger(
            service
        )

        self.consensus = Consensus()

    def enhance(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        review = self.reviewer.review(
            decision
        )

        challenge = self.challenger.review(
            decision
        )

        return self.consensus.combine(
            review,
            challenge,
        )

    def enhance_many(
        self,
        decisions: list[DecisionResult],
    ) -> list[ReasoningResult]:

        return [
            self.enhance(
                decision
            )
            for decision in decisions
        ]
    