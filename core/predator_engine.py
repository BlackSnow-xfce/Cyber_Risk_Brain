from __future__ import annotations

from typing import Any

from connectors.connector_manager import ConnectorManager

from core.graph import AssessmentGraph
from core.mapper import finding_to_universal

from analysis.risk_engine import RiskEngine
from analysis.attack_path_analyzer import AttackPathAnalyzer
from analysis.mitre_analyzer import MitreAnalyzer
from analysis.detection_analyzer import DetectionAnalyzer


class PredatorEngine:
    """
    Central orchestration engine of PredatorAI.

    Responsible for executing the complete reasoning pipeline.
    """

    def __init__(self) -> None:

        self.connector_manager = ConnectorManager()

        self.graph = AssessmentGraph()

        self.risk_engine = RiskEngine()

        self.attack_path = AttackPathAnalyzer()

        self.mitre = MitreAnalyzer()

        self.detection = DetectionAnalyzer()

        self.findings: list[Any] = []

        self.universal_findings: list[Any] = []

        self.graph_nodes: list[dict[str, Any]] = []

        self.graph_edges: list[tuple[str, str]] = []

    # -----------------------------------------------------
    # Connector Stage
    # -----------------------------------------------------

    def load_connectors(self) -> None:

        self.connector_manager.load_connectors()

    def show_enabled_connectors(self) -> None:

        self.connector_manager.show_enabled_connectors()

    def collect_findings(self) -> list[Any]:

        findings: list[Any] = []

        for connector in self.connector_manager.connectors:

            findings.extend(
                connector.get_findings()
            )

        self.findings = findings

        return findings

    # -----------------------------------------------------
    # Mapping Stage
    # -----------------------------------------------------

    def map_findings(self) -> list[Any]:

        mapped: list[Any] = []

        for finding in self.findings:

            mapped.append(
                finding_to_universal(
                    finding
                )
            )

        self.universal_findings = mapped

        return mapped

    # -----------------------------------------------------
    # Graph Stage
    # -----------------------------------------------------

    def build_graph(self) -> None:

        for finding in self.findings:

            self.graph.add_node(

                finding.name,

                severity=finding.severity,

                exposed=finding.exposed,

                criticality=finding.criticality,

                detection=finding.detection,

                threat_intel=finding.threat_intel,

                mitre=finding.mitre,

                owner=finding.owner,

                sla_days=finding.sla_days,
            )

            if finding.name == "Exposed VM":

                self.graph.add_edge(
                    "Internet",
                    finding.name,
                )

            if finding.name == "Internal Admin Panel":

                self.graph.add_edge(
                    "Exposed VM",
                    finding.name,
                )

            if finding.name == "Wiz Finding":

                self.graph.add_edge(
                    finding.name,
                    "Tier0 Asset",
                )

        self.graph_nodes = self.graph.nodes

        self.graph_edges = self.graph.edges

            # -----------------------------------------------------
    # Risk & Decision Stage
    # -----------------------------------------------------

    def analyze_risk(self) -> dict[str, Any]:

        return self.risk_engine.build_graph_summary(
            self.graph_nodes
        )

    def analyze_decisions(self):

        return self.risk_engine.analyze_nodes(
            self.graph_nodes
        )

    def analyze_team_risk(self):

        findings = []

        for node in self.graph_nodes:

            prepared = dict(node)

            prepared["risk_score"] = (
                self.risk_engine.calculate_risk_score(
                    prepared
                )
            )

            findings.append(
                prepared
            )

        return self.risk_engine.calculate_team_risk(
            findings
        )

    # -----------------------------------------------------
    # Detection Analysis
    # -----------------------------------------------------

    def analyze_detection(self) -> None:

        self.detection.detect_detection_gaps(
            self.graph_nodes
        )

        self.detection.detection_coverage_score(
            self.graph_nodes
        )

    # -----------------------------------------------------
    # MITRE Analysis
    # -----------------------------------------------------

    def analyze_mitre(self) -> None:

        self.mitre.show_mitre_techniques(
            self.graph_nodes
        )

        self.mitre.mitre_detection_analysis(
            self.graph_nodes
        )

    # -----------------------------------------------------
    # Attack Path Analysis
    # -----------------------------------------------------

    def analyze_attack_paths(self) -> None:

        self.attack_path.show_attack_paths(
            self.graph_edges
        )

        self.attack_path.find_exposed_paths(
            self.graph_edges
        )

        self.attack_path.detect_critical_paths(
            self.graph_edges
        )

        self.attack_path.crown_jewel_analysis(
            self.graph_edges
        )

    # -----------------------------------------------------
    # Reporting Stage
    # -----------------------------------------------------

    def print_universal_findings(self) -> None:

        print()

        print("Universal Findings")

        print("------------------------------")

        for finding in self.universal_findings:

            print(
                f"{finding.source}"
                f" | "
                f"{finding.title}"
                f" | "
                f"{finding.vendor_severity}"
            )

    def print_decision_summary(
        self,
        decisions,
    ) -> None:

        print()

        print("PredatorAI Decisions")

        print("------------------------------")

        for decision in decisions:

            print()

            print(
                decision.finding_id
            )

            print(
                f"Priority : {decision.priority.value}"
            )

            print(
                f"Action   : {decision.action.value}"
            )

            print(
                f"Decision : {decision.decision}"
            )

            print(
                f"Confidence : "
                f"{decision.confidence.score:.0f}%"
            )

            print()

            for line in decision.explanation:

                print(line)

                    # -----------------------------------------------------
    # Main Pipeline
    # -----------------------------------------------------

    def run(self) -> dict[str, Any]:

        print()
        print("========================================")
        print(" PredatorAI")
        print(" Cyber Reasoning Platform")
        print("========================================")
        print()

        self.load_connectors()

        self.show_enabled_connectors()

        self.collect_findings()

        self.map_findings()

        self.print_universal_findings()

        self.build_graph()

        graph_summary = self.analyze_risk()

        decisions = self.analyze_decisions()

        team_risk = self.analyze_team_risk()

        self.analyze_detection()

        self.analyze_mitre()

        self.analyze_attack_paths()

        self.graph.prioritize_findings()

        self.graph.executive_summary()

        self.graph.remediation_recommendations()

        self.print_decision_summary(
            decisions
        )

        return {
            "findings": self.findings,
            "universal_findings": self.universal_findings,
            "graph": self.graph,
            "graph_summary": graph_summary,
            "team_risk": team_risk,
            "decisions": decisions,
        }

    # -----------------------------------------------------
    # Helper Functions
    # -----------------------------------------------------

    def graph_risk(self) -> int:

        return self.risk_engine.calculate_risk(
            self.graph_nodes
        )

    def graph_risk_level(self) -> str:

        return self.risk_engine.get_risk_level(
            self.graph_risk()
        )

    def graph_nodes_count(self) -> int:

        return len(
            self.graph_nodes
        )

    def findings_count(self) -> int:

        return len(
            self.findings
        )

    def decision_count(self) -> int:

        return len(
            self.risk_engine.analyze_nodes(
                self.graph_nodes
            )
        )

    def export(self) -> dict[str, Any]:

        return self.run()

    def __repr__(self) -> str:

        return (
            "PredatorEngine("
            f"findings={self.findings_count()}, "
            f"nodes={self.graph_nodes_count()}, "
            f"risk='{self.graph_risk_level()}'"
            ")"
        )