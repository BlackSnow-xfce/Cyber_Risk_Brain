from __future__ import annotations

from core.ai.reasoning_engine import ReasoningEngine
from core.ai.reasoning_result import ReasoningResult

from core.decision.decision_trace import DecisionTrace
from core.decision.decision_trace_builder import DecisionTraceBuilder
from core.decision.models import DecisionResult


class DecisionService:
    """
    PredatorAI Decision Orchestrator.

    Coordinates the Decision Engine,
    AI Layer and Decision Trace.

    This is the primary entry point for
    consumers like the Dashboard,
    Story Engine and REST API.
    """

    def __init__(
        self,
    ) -> None:

        self.reasoning = ReasoningEngine()

        self.trace_builder = DecisionTraceBuilder()

    def build_trace(
        self,
        decision: DecisionResult,
    ) -> DecisionTrace:

        reasoning: ReasoningResult = (
            self.reasoning.enhance(
                decision
            )
        )

        return self.trace_builder.build(
            decision,
            reasoning,
        )
    