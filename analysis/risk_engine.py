from __future__ import annotations

from typing import Any

from core.decision.decision_engine import DecisionEngine
from core.decision.models import DecisionResult


class RiskEngine:
    """
    Central risk and decision orchestration engine for PredatorAI.

    The engine keeps the existing risk calculations and adds the
    Decision Engine as the reasoning layer.
    """

    def __init__(self) -> None:
        self.decision_engine = DecisionEngine()

    def calculate_risk(
        self,
        nodes: list[dict[str, Any]],
    ) -> int:
        """
        Calculates the accumulated graph risk score.
        """

        score = 0

        for node in nodes:
            criticality = self._get_criticality(node)

            if criticality == "CRITICAL":
                score += 10
            elif criticality == "HIGH":
                score += 7
            elif criticality == "MEDIUM":
                score += 4
            else:
                score += 1

        return score

    @staticmethod
    def get_risk_level(
        risk: int,
    ) -> str:
        """
        Converts the accumulated graph risk score into a risk level.
        """

        if risk >= 20:
            return "CRITICAL"

        if risk >= 10:
            return "HIGH"

        if risk >= 5:
            return "MEDIUM"

        return "LOW"

    def calculate_business_risk(
        self,
        node: dict[str, Any],
    ) -> str:
        """
        Calculates the business risk level of a single graph node.
        """

        score = 0
        criticality = self._get_criticality(node)

        if criticality == "CRITICAL":
            score += 5
        elif criticality == "HIGH":
            score += 4
        elif criticality == "MEDIUM":
            score += 2
        else:
            score += 1

        if bool(node.get("exposed", False)):
            score += 3

        if not bool(node.get("detection", False)):
            score += 2

        if bool(node.get("threat_intel", False)):
            score += 3

        if score >= 12:
            return "CRITICAL"

        if score >= 8:
            return "HIGH"

        if score >= 4:
            return "MEDIUM"

        return "LOW"

    def calculate_risk_score(
        self,
        node: dict[str, Any],
    ) -> int:
        """
        Calculates the normalized risk score of a single graph node.
        """

        score = 0
        criticality = self._get_criticality(node)

        if criticality == "CRITICAL":
            score += 40
        elif criticality == "HIGH":
            score += 30
        elif criticality == "MEDIUM":
            score += 20
        else:
            score += 10

        if bool(node.get("exposed", False)):
            score += 20

        if not bool(node.get("detection", False)):
            score += 15

        if bool(node.get("threat_intel", False)):
            score += 15

        if node.get("mitre"):
            score += 10

        return min(score, 100)

    def explain_business_risk(
        self,
        node: dict[str, Any],
    ) -> list[str]:
        """
        Returns the main factors that influence business risk.
        """

        reasons: list[str] = []
        criticality = self._get_criticality(node)

        if bool(node.get("exposed", False)):
            reasons.append("Internet exposed")

        if not bool(node.get("detection", False)):
            reasons.append("No detection coverage")

        if bool(node.get("threat_intel", False)):
            reasons.append("Threat intelligence match")

        if criticality == "CRITICAL":
            reasons.append("Business critical asset")
        elif criticality == "HIGH":
            reasons.append("High business criticality")

        if node.get("mitre"):
            reasons.append("MITRE ATT&CK context available")

        if not reasons:
            reasons.append("No major risk amplifiers detected")

        return reasons

    def recommend_actions(
        self,
        node: dict[str, Any],
    ) -> list[str]:
        """
        Preserves the existing compact recommendation output.
        """

        recommendations: list[str] = []

        if bool(node.get("exposed", False)):
            recommendations.append(
                "Restrict or remove external exposure"
            )

        if not bool(node.get("detection", False)):
            recommendations.append(
                "Enable detection coverage"
            )

        if bool(node.get("threat_intel", False)):
            recommendations.append(
                "Investigate active threat exposure"
            )

        if self._get_criticality(node) == "CRITICAL":
            recommendations.append(
                "Prioritize immediate remediation"
            )

        if not recommendations:
            recommendations.append(
                "Continue monitoring"
            )

        return recommendations

    def analyze_node(
        self,
        node: dict[str, Any],
    ) -> DecisionResult:
        """
        Runs the complete PredatorAI decision process for one node.
        """

        prepared_node = self._prepare_node(node)

        return self.decision_engine.analyze(
            prepared_node
        )

    def analyze_nodes(
        self,
        nodes: list[dict[str, Any]],
    ) -> list[DecisionResult]:
        """
        Runs the complete PredatorAI decision process for all nodes.
        """

        decisions: list[DecisionResult] = []

        for node in nodes:
            decisions.append(
                self.analyze_node(node)
            )

        return decisions

    def analyze_node_as_dict(
        self,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Returns a serializable decision result for APIs and dashboards.
        """

        return self.analyze_node(node).to_dict()

    def analyze_nodes_as_dict(
        self,
        nodes: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Returns serializable decision results for APIs and dashboards.
        """

        return [
            decision.to_dict()
            for decision in self.analyze_nodes(nodes)
        ]

    def build_node_summary(
        self,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Combines the legacy risk output with the Decision Engine output.
        """

        prepared_node = self._prepare_node(node)

        decision = self.decision_engine.analyze(
            prepared_node
        )

        return {
            "name": prepared_node["name"],
            "owner": prepared_node["owner"],
            "criticality": prepared_node["criticality"],
            "risk_score": self.calculate_risk_score(
                prepared_node
            ),
            "business_risk": self.calculate_business_risk(
                prepared_node
            ),
            "reasons": self.explain_business_risk(
                prepared_node
            ),
            "legacy_recommendations": self.recommend_actions(
                prepared_node
            ),
            "decision": decision.to_dict(),
        }

    def build_graph_summary(
        self,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Builds a full graph-level risk and decision summary.
        """

        node_summaries = [
            self.build_node_summary(node)
            for node in nodes
        ]

        graph_risk = self.calculate_risk(nodes)

        sorted_nodes = sorted(
            node_summaries,
            key=lambda item: item["risk_score"],
            reverse=True,
        )

        highest_risk_node = (
            sorted_nodes[0]
            if sorted_nodes
            else None
        )

        return {
            "graph_risk_score": graph_risk,
            "graph_risk_level": self.get_risk_level(
                graph_risk
            ),
            "finding_count": len(nodes),
            "highest_risk_node": highest_risk_node,
            "nodes": sorted_nodes,
        }

    def calculate_team_risk(
        self,
        findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Aggregates findings and risk scores by owner or team.
        """

        teams: dict[str, dict[str, Any]] = {}

        for finding in findings:
            team = str(
                finding.get("owner") or "Unknown"
            )

            risk_score = self._extract_risk_score(
                finding
            )

            title = str(
                finding.get("title")
                or finding.get("name")
                or "Unknown finding"
            )

            if team not in teams:
                teams[team] = {
                    "team": team,
                    "finding_count": 0,
                    "total_risk": 0,
                    "average_risk": 0,
                    "highest_risk": 0,
                    "highest_finding": "",
                }

            teams[team]["finding_count"] += 1
            teams[team]["total_risk"] += risk_score

            if risk_score > teams[team]["highest_risk"]:
                teams[team]["highest_risk"] = risk_score
                teams[team]["highest_finding"] = title

        for team_data in teams.values():
            finding_count = team_data["finding_count"]

            if finding_count > 0:
                team_data["average_risk"] = round(
                    team_data["total_risk"]
                    / finding_count,
                    2,
                )

        return sorted(
            teams.values(),
            key=lambda item: item["total_risk"],
            reverse=True,
        )

    def _prepare_node(
        self,
        node: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalizes graph nodes before they enter the Decision Engine.
        """

        prepared_node = dict(node)

        prepared_node["name"] = str(
            prepared_node.get("name")
            or prepared_node.get("title")
            or "Unknown"
        )

        prepared_node["criticality"] = (
            self._get_criticality(prepared_node)
        )

        prepared_node["owner"] = str(
            prepared_node.get("owner")
            or "Unknown"
        )

        prepared_node["exposed"] = bool(
            prepared_node.get("exposed", False)
        )

        prepared_node["detection"] = bool(
            prepared_node.get("detection", False)
        )

        prepared_node["threat_intel"] = bool(
            prepared_node.get("threat_intel", False)
        )

        if prepared_node.get("sla_days") is not None:
            try:
                prepared_node["sla_days"] = int(
                    prepared_node["sla_days"]
                )
            except (TypeError, ValueError):
                prepared_node["sla_days"] = None

        prepared_node["risk_score"] = (
            self.calculate_risk_score(
                prepared_node
            )
        )

        return prepared_node

    @staticmethod
    def _get_criticality(
        node: dict[str, Any],
    ) -> str:
        """
        Normalizes criticality values.
        """

        criticality = str(
            node.get("criticality", "LOW")
        ).strip().upper()

        allowed_values = {
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
        }

        if criticality not in allowed_values:
            return "LOW"

        return criticality

    def _extract_risk_score(
        self,
        finding: dict[str, Any],
    ) -> int:
        """
        Uses an existing risk score or calculates one from node context.
        """

        existing_score = finding.get("risk_score")

        if existing_score is not None:
            try:
                return max(
                    0,
                    min(
                        int(existing_score),
                        100,
                    ),
                )
            except (TypeError, ValueError):
                pass

        return self.calculate_risk_score(
            finding
        )
    