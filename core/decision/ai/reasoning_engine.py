from __future__ import annotations

from core.decision.ai.challenger import Challenger
from core.decision.ai.decision_memory import (
    DecisionMemory,
)
from core.decision.ai.factory import LLMFactory
from core.decision.ai.judge import Judge
from core.decision.ai.reasoning_result import (
    ReasoningResult,
)
from core.decision.ai.reasoning_service import (
    ReasoningService,
)
from core.decision.ai.reviewer import Reviewer

from core.decision.models import DecisionResult


class ReasoningEngine:
    """
    PredatorAI AI Orchestrator.

    Decision
        ↓
    Reviewer
        ↓
    Challenger
        ↓
    Judge
        ↓
    Memory
    """

    def __init__(
        self,
        provider: str = "local",
    ) -> None:

        llm = LLMFactory.create(
            provider
        )

        service = ReasoningService(
            llm
        )

        self.reviewer = Reviewer(
            service
        )

        self.challenger = Challenger(
            service
        )

        self.judge = Judge()

        self.memory = DecisionMemory()

    def enhance(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        reviewer_result = (
            self.reviewer.review(
                decision
            )
        )

        challenger_result = (
            self.challenger.review(
                decision
            )
        )

        final_result = self.judge.evaluate(

            reviewer_result,

            challenger_result,

        )

        self.memory.add(

            decision,

            final_result,

        )

        return final_result

    def enhance_many(
        self,
        decisions: list[
            DecisionResult
        ],
    ) -> list[
        ReasoningResult
    ]:

        return [

            self.enhance(
                decision
            )

            for decision in decisions

        ]

    def history(self):

        return self.memory.all()

    def latest(self):

        return self.memory.latest()

    def history_count(
        self,
    ) -> int:

        return self.memory.count()

    def clear_history(
        self,
    ) -> None:

        self.memory.clear()
        