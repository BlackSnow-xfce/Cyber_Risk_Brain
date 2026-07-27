from __future__ import annotations

from core.decision.models import DecisionPriority


class PriorityEngine:
    """
    Determines the priority from the calculated risk score.
    """

    def calculate(
        self,
        risk_score: int,
    ) -> DecisionPriority:

        if risk_score >= 90:
            return DecisionPriority.CRITICAL

        if risk_score >= 75:
            return DecisionPriority.HIGH

        if risk_score >= 50:
            return DecisionPriority.MEDIUM

        if risk_score >= 25:
            return DecisionPriority.LOW

        return DecisionPriority.INFORMATIONAL
    