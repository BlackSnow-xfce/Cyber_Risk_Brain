from __future__ import annotations

from core.ai.reasoning_engine import ReasoningEngine

from core.decision.decision_context import DecisionContext
from core.decision.decision_explainer import DecisionExplainer
from core.decision.decision_trace import DecisionTrace
from core.decision.decision_trace_builder import DecisionTraceBuilder
from core.decision.models import DecisionResult


class DecisionService:
    """
    Central orchestration layer of PredatorAI.

    Pipeline

    DecisionResult
            │
            ▼
      AI Reasoning
            │
            ▼
     DecisionContext
            │
            ▼
    DecisionTraceBuilder
            │
            ▼
      DecisionTrace
            │
            ▼
    DecisionExplainer
            │
            ▼
      Final DecisionTrace
    """

    def __init__(
        self,
    ) -> None:

        self.reasoning = ReasoningEngine()

        self.trace_builder = (
            DecisionTraceBuilder()
        )

        self.explainer = (
            DecisionExplainer()
        )

    def build_trace(
        self,
        decision: DecisionResult,
    ) -> DecisionTrace:

        reasoning = self.reasoning.enhance(
            decision
        )

        context = DecisionContext(

            decision=decision,

            reasoning=reasoning,

        )

        trace = self.trace_builder.build(
            context
        )

        trace.executive_summary = (
            self.explainer.executive(
                trace
            )
        )

        trace.soc_summary = (
            self.explainer.soc(
                trace
            )
        )

        trace.technical_summary = (
            self.explainer.technical(
                trace
            )
        )

        return trace
    