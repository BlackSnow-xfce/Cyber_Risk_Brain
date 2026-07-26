from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from core.decision.models import DecisionResult


class DashboardDataBuilder:
    """
    Adapts the PredatorEngine.run() result to a dashboard-friendly
    JSON structure. No business logic is calculated here.
    """

    def build(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        decisions: list[DecisionResult] = result.get(
            "decisions",
            [],
        )

        return {
            "summary": result.get("graph_summary", {}),
            "graph_summary": result.get("graph_summary", {}),
            "team_risk": result.get("team_risk", {}),
            "decision_count": len(decisions),
            "decisions": [
                self._decision_to_dict(d)
                for d in decisions
            ],
            "reasoning_results": result.get(
                "reasoning_results",
                [],
            ),
            "story_bundles": result.get(
                "story_bundles",
                [],
            ),
            "reports": result.get(
                "reports",
                [],
            ),
        }

    def _decision_to_dict(
        self,
        decision: DecisionResult,
    ) -> dict[str, Any]:

        if hasattr(decision, "to_dict"):
            data = decision.to_dict()
        elif is_dataclass(decision):
            data = asdict(decision)
        else:
            data = dict(decision)

        data["risk_score"] = decision.metadata.get(
            "risk_score",
            0,
        )

        return data
    