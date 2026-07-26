from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.decision.models import AttackReasoning


class DashboardDataBuilder:
    """
    Converts AttackReasoning objects into a dashboard-friendly structure.
    """

    def build(self, findings: list[AttackReasoning]) -> dict[str, Any]:
        total = len(findings)

        critical = sum(1 for f in findings if f.score >= 90)
        high = sum(1 for f in findings if 75 <= f.score < 90)
        medium = sum(1 for f in findings if 50 <= f.score < 75)
        low = sum(1 for f in findings if f.score < 50)

        highest = None
        if findings:
            highest = max(findings, key=lambda x: x.score)

        return {
            "summary": {
                "total_findings": total,
                "critical": critical,
                "high": high,
                "medium": medium,
                "low": low,
            },
            "highest_risk": asdict(highest) if highest else None,
            "findings": [asdict(f) for f in findings],
        }