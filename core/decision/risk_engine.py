from __future__ import annotations

from typing import Any


class RiskEngine:
    """
    Calculates the overall cyber risk score for a finding.

    This engine is the single source of truth for risk
    calculation inside PredatorAI.
    """

    def calculate(
        self,
        node: dict[str, Any],
    ) -> int:

        score = 0

        criticality = str(
            node.get(
                "criticality",
                "LOW",
            )
        ).upper()

        if criticality == "CRITICAL":
            score += 40

        elif criticality == "HIGH":
            score += 30

        elif criticality == "MEDIUM":
            score += 20

        else:
            score += 10

        if node.get(
            "exposed",
            False,
        ):
            score += 20

        if not node.get(
            "detection",
            True,
        ):
            score += 15

        if node.get(
            "threat_intel",
            False,
        ):
            score += 15

        if node.get(
            "mitre",
        ):
            score += 10

        return min(
            score,
            100,
        )
    