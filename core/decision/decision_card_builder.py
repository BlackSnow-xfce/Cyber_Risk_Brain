from __future__ import annotations

from core.decision.decision_card import DecisionCard
from core.decision.decision_trace import DecisionTrace


class DecisionCardBuilder:
    """
    Builds a UI-ready DecisionCard from a DecisionTrace.
    """

    def build(
        self,
        trace: DecisionTrace,
    ) -> DecisionCard:

        return DecisionCard(

            title=self._title(trace),

            decision=trace.decision,

            priority=trace.priority,

            risk_score=trace.risk_score,

            confidence=trace.confidence,

            ai_verdict=trace.ai_verdict,

            business_impact=trace.business_impact,

            reasons=list(trace.reasons),

            recommendations=list(
                trace.recommendations
            ),

            counter_arguments=list(
                trace.counter_arguments
            ),

            executive_summary=(
                trace.executive_summary
            ),

            technical_summary=(
                trace.technical_summary
            ),
        )

    def _title(
        self,
        trace: DecisionTrace,
    ) -> str:

        priority = str(trace.priority).upper()

        if "CRITICAL" in priority:
            return "Patch Immediately"

        if "HIGH" in priority:
            return "Investigate Immediately"

        if "MEDIUM" in priority:
            return "Review Required"

        return "Monitor"

