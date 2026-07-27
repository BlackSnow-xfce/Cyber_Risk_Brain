from __future__ import annotations

from core.decision.models import DecisionResult

from core.ai.decision_memory import DecisionMemory
from core.ai.factory import LLMFactory
from core.ai.judge import Judge
from core.ai.reasoning_result import ReasoningResult
from core.ai.reasoning_service import ReasoningService
from core.ai.reviewer import Reviewer
from core.ai.challenger import Challenger


class ReasoningEngine:
    """
    PredatorAI AI Orchestrator.

    Workflow

        Decision
            │
            ▼
        Reviewer
            │
            ▼
        Challenger
            │
            ▼
          Judge
            │
            ▼
     Decision Memory
            │
            ▼
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

        self.judge = Judge()

        self.memory = DecisionMemory()

    def enhance(
        self,
        decision: DecisionResult,
    ) -> ReasoningResult:

        reviewer_result = self.reviewer.review(
            decision
        )

        challenger_result = self.challenger.review(
            decision
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
        decisions: list[DecisionResult],
    ) -> list[ReasoningResult]:

        return [

            self.enhance(
                decision
            )

            for decision in decisions

        ]

    def history(self):

        return self.memory.all()

    def history_count(self) -> int:

        return self.memory.count()

    def clear_history(self) -> None:

        self.memory.clear()
        