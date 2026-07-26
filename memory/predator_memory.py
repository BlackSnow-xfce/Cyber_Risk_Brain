from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from core.decision.models import DecisionResult


class PredatorMemory:
    """
    In-memory knowledge base used by PredatorAI.

    Stores decisions, findings and historical trends.
    """

    def __init__(self) -> None:

        self.created_at = datetime.utcnow()

        self.decisions: list[DecisionResult] = []

        self.asset_history: dict[
            str,
            list[DecisionResult]
        ] = defaultdict(list)

        self.team_history: dict[
            str,
            list[DecisionResult]
        ] = defaultdict(list)

        self.priority_history: dict[
            str,
            list[DecisionResult]
        ] = defaultdict(list)

        self.metadata: dict[str, Any] = {}

    # --------------------------------------------------
    # Decision Storage
    # --------------------------------------------------

    def add(
        self,
        decision: DecisionResult,
        owner: str = "Unknown",
    ) -> None:

        self.decisions.append(
            decision
        )

        self.asset_history[
            decision.finding_id
        ].append(
            decision
        )

        self.team_history[
            owner
        ].append(
            decision
        )

        self.priority_history[
            decision.priority.value
        ].append(
            decision
        )

    def add_many(
        self,
        decisions: list[DecisionResult],
        owner_lookup: dict[str, str],
    ) -> None:

        for decision in decisions:

            owner = owner_lookup.get(
                decision.finding_id,
                "Unknown",
            )

            self.add(
                decision,
                owner,
            )

    # --------------------------------------------------
    # Counts
    # --------------------------------------------------

    def total_decisions(
        self,
    ) -> int:

        return len(
            self.decisions
        )

    def total_assets(
        self,
    ) -> int:

        return len(
            self.asset_history
        )

    def total_teams(
        self,
    ) -> int:

        return len(
            self.team_history
        )
    
        # --------------------------------------------------
    # Queries
    # --------------------------------------------------

    def get_asset_history(
        self,
        asset: str,
    ) -> list[DecisionResult]:

        return self.asset_history.get(
            asset,
            [],
        )

    def get_team_history(
        self,
        team: str,
    ) -> list[DecisionResult]:

        return self.team_history.get(
            team,
            [],
        )

    def get_priority_history(
        self,
        priority: str,
    ) -> list[DecisionResult]:

        return self.priority_history.get(
            priority,
            [],
        )

    # --------------------------------------------------
    # Statistics
    # --------------------------------------------------

    def priority_statistics(
        self,
    ) -> dict[str, int]:

        return {
            priority: len(history)
            for priority, history
            in self.priority_history.items()
        }

    def team_statistics(
        self,
    ) -> dict[str, int]:

        return {
            team: len(history)
            for team, history
            in self.team_history.items()
        }

    def asset_statistics(
        self,
    ) -> dict[str, int]:

        return {
            asset: len(history)
            for asset, history
            in self.asset_history.items()
        }

    # --------------------------------------------------
    # Highest Risks
    # --------------------------------------------------

    def highest_risk_assets(
        self,
        limit: int = 10,
    ) -> list[DecisionResult]:

        ordered = sorted(
            self.decisions,
            key=lambda decision:
                decision.metadata.get(
                    "risk_score",
                    0,
                ),
            reverse=True,
        )

        return ordered[:limit]

    def critical_findings(
        self,
    ) -> list[DecisionResult]:

        return [
            decision
            for decision in self.decisions
            if decision.priority.value == "critical"
        ]

    # --------------------------------------------------
    # Search
    # --------------------------------------------------

    def search(
        self,
        keyword: str,
    ) -> list[DecisionResult]:

        keyword = keyword.lower()

        results = []

        for decision in self.decisions:

            if keyword in decision.finding_id.lower():

                results.append(
                    decision
                )

        return results
    
        # --------------------------------------------------
    # Trends
    # --------------------------------------------------

    def trend(self) -> dict[str, int]:

        return {
            "decisions": self.total_decisions(),
            "assets": self.total_assets(),
            "teams": self.total_teams(),
            "critical": len(
                self.critical_findings()
            ),
        }

    # --------------------------------------------------
    # Metadata
    # --------------------------------------------------

    def set_metadata(
        self,
        key: str,
        value: Any,
    ) -> None:

        self.metadata[key] = value

    def get_metadata(
        self,
        key: str,
        default: Any = None,
    ) -> Any:

        return self.metadata.get(
            key,
            default,
        )

    # --------------------------------------------------
    # Export
    # --------------------------------------------------

    def export(self) -> dict[str, Any]:

        return {

            "created_at":
                self.created_at.isoformat(),

            "decision_count":
                self.total_decisions(),

            "asset_count":
                self.total_assets(),

            "team_count":
                self.total_teams(),

            "priority_statistics":
                self.priority_statistics(),

            "team_statistics":
                self.team_statistics(),

            "asset_statistics":
                self.asset_statistics(),

            "trend":
                self.trend(),
        }

    # --------------------------------------------------
    # Representation
    # --------------------------------------------------

    def __repr__(
        self,
    ) -> str:

        return (

            "PredatorMemory("

            f"decisions={self.total_decisions()}, "

            f"assets={self.total_assets()}, "

            f"teams={self.total_teams()})"

        )