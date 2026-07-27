from __future__ import annotations

from dataclasses import asdict
from typing import Any

from core.decision.decision_card_builder import (
    DecisionCardBuilder,
)
from core.decision.decision_trace import DecisionTrace


class DashboardDataBuilder:
    """
    Converts DecisionTrace objects into
    dashboard-ready JSON.
    """

    def __init__(self) -> None:

        self.card_builder = DecisionCardBuilder()

    def build(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        traces: list[DecisionTrace] = result.get(
            "decision_traces",
            [],
        )

        cards = [

            asdict(
                self.card_builder.build(trace)
            )

            for trace in traces

        ]

        return {

            "summary": result.get(
                "graph_summary",
                {},
            ),

            "graph_summary": result.get(
                "graph_summary",
                {},
            ),

            "team_risk": result.get(
                "team_risk",
                {},
            ),

            "decision_count": len(cards),

            "decision": (
                cards[0]
                if cards
                else None
            ),

            "decisions": cards,

            "feed": cards[:5],

            "business": result.get(
                "business",
                {},
            ),

            "attack_path": result.get(
                "attack_path",
                {},
            ),

            "timeline": result.get(
                "timeline",
                [],
            ),

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
    