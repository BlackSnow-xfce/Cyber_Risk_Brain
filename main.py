from connectors.connector_manager import ConnectorManager
from connectors.wiz_connector import WizConnector
from core.models import Finding
from analysis.attack_path_analyzer import AttackPathAnalyzer
from analysis.mitre_analyzer import MitreAnalyzer
from analysis.detection_analyzer import DetectionAnalyzer
from analysis.risk_engine import RiskEngine
from wiz_client import WizClient
from risk_scorer import RiskScorer
from core.graph import AssessmentGraph
from settings import WIZ_ENABLED, JIRA_ENABLED, NEO4J_ENABLED, REDIS_ENABLED
from core.mapper import finding_to_universal

graph = AssessmentGraph()

print("Enabled Connectors:")

if WIZ_ENABLED == "true":
    print("- Wiz enabled")

if JIRA_ENABLED == "true":
    print("- Jira enabled")

if NEO4J_ENABLED == "true":
    print("- Neo4j enabled")

if REDIS_ENABLED == "true":
    print("- Redis enabled")

connector_manager = ConnectorManager()

connector_manager.load_connectors()

connector_manager.show_enabled_connectors()

findings = []

for connector in connector_manager.connectors:

    findings.extend(
        connector.get_findings()
    )
    
universal_findings = []

for finding in findings:

    universal_finding = finding_to_universal(
        finding
    )

    universal_findings.append(
        universal_finding
    )

    print("\nUniversal Findings:")

for finding in universal_findings:

    print(
        finding.source,
        "|",
        finding.title,
        "|",
        finding.vendor_severity
    )

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
    if finding.name == "Exposed VM":
        graph.add_edge("Internet", finding.name)

    if finding.name == "Internal Admin Panel":
        graph.add_edge("Exposed VM", finding.name)

    if finding.name == "Wiz Finding":
        graph.add_edge(finding.name, "Tier0 Asset")

graph.show_graph()

if WIZ_ENABLED == "true":

    wiz = WizClient()

    wiz.test_connection()

    wiz.test_api()

else:

    print("Wiz connector disabled")

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
print("Business Risk Evaluation:")

for node in graph.nodes:

    business_risk = risk_engine.calculate_business_risk(node)

    print(
        f"{node['name']} | "
        f"Vendor Severity: {node['severity']} | "
        f"Business Risk: {business_risk}"
    )

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
