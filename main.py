from assessment_graph import AssessmentGraph
from wiz_client import WizClient
from risk_scorer import RiskScorer

graph = AssessmentGraph()

findings = [
    (
        "Wiz Finding",
        "CRITICAL",
        True,
        "CRITICAL",
        False,
        True,
        "Privilege Escalation",
        "Cloud Team"
    ),

    (
        "Public S3 Bucket",
        "HIGH",
        True,
        "HIGH",
        True,
        False,
        "Collection",
        "Storage Team"
    ),

    (
        "Internal Admin Panel",
        "HIGH",
        False,
        "MEDIUM",
        False,
        False,
        "Lateral Movement",
        "Infrastructure Team"
    ),

    (
        "Exposed VM",
        "MEDIUM",
        True,
        "LOW",
        False,
        True,
        "Initial Access",
        "Server Team"
    )
]

for (
    finding,
    severity,
    exposed,
    criticality,
    detection,
    threat_intel,
    mitre,
    owner
) in findings:

    graph.add_node(
    finding,
    severity,
    exposed=exposed,
    criticality=criticality,
    detection=detection,
    threat_intel=threat_intel,
    mitre=mitre,
    owner=owner
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

graph_risk = graph.calculate_risk()

print("Graph Risk:", graph_risk)

print(graph.calculate_risk())

print(graph.get_risk_level())

graph.show_attack_paths()

graph.find_exposed_paths()

graph.detect_critical_paths()

graph.prioritize_findings()

graph.detect_detection_gaps()

graph.detection_coverage_score()

graph.executive_summary()

graph.show_mitre_techniques()

graph.mitre_detection_analysis()

graph.crown_jewel_analysis()

graph.remediation_recommendations()
