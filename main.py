from connectors.wiz_connector import WizConnector
from core.models import Finding
from analysis.attack_path_analyzer import AttackPathAnalyzer
from analysis.mitre_analyzer import MitreAnalyzer
from analysis.detection_analyzer import DetectionAnalyzer
from analysis.risk_engine import RiskEngine
from wiz_client import WizClient
from risk_scorer import RiskScorer
from core.graph import AssessmentGraph

graph = AssessmentGraph()

wiz_connector = WizConnector()

findings = wiz_connector.get_findings()

for finding in findings:
    graph.add_node(
    finding.name,
    severity=finding.severity,
    exposed=finding.exposed,
    criticality=finding.criticality,
    detection=finding.detection,
    threat_intel=finding.threat_intel,
    mitre=finding.mitre,
    owner=finding.owner,
    sla_days=finding.sla_days
)
    if finding == "Exposed VM":
        graph.add_edge("Internet", finding)

    if finding == "Internal Admin Panel":
        graph.add_edge("Exposed VM", finding)

    if finding == "Wiz Finding":
        graph.add_edge(finding, "Tier0 Asset")

graph.show_graph()

wiz = WizClient()
wiz.test_connection()
wiz.test_api()

scorer = RiskScorer()

score = scorer.calculate_score("critical")

print("Risk Score:", score)

risk_engine = RiskEngine()

graph_risk = risk_engine.calculate_risk(
    graph.nodes
)

print("Graph Risk:", graph_risk)

print(graph.calculate_risk())

print(
    risk_engine.get_risk_level(graph_risk)
)

attack_path_analyzer = AttackPathAnalyzer()

attack_path_analyzer.show_attack_paths(
    graph.edges
)

attack_path_analyzer.find_exposed_paths(
    graph.edges
)

attack_path_analyzer.detect_critical_paths(
    graph.edges
)

graph.prioritize_findings()

detection_analyzer = DetectionAnalyzer()

detection_analyzer.detect_detection_gaps(
    graph.nodes
)

detection_analyzer.detection_coverage_score(
    graph.nodes
)

mitre_analyzer = MitreAnalyzer()

mitre_analyzer.show_mitre_techniques(
    graph.nodes
)

graph.executive_summary()

mitre_analyzer.mitre_detection_analysis(
    graph.nodes
)

attack_path_analyzer.crown_jewel_analysis(
    graph.edges
)

graph.remediation_recommendations()
