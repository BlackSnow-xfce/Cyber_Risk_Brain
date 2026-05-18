from assessment_graph import AssessmentGraph
from wiz_client import WizClient
from risk_scorer import RiskScorer

graph = AssessmentGraph()

findings = [
    ("Wiz Finding", "CRITICAL", True, "CRITICAL"),
    ("Public S3 Bucket", "HIGH", True, "HIGH"),
    ("Internal Admin Panel", "HIGH", False, "MEDIUM"),
    ("Exposed VM", "MEDIUM", True, "LOW")
]

for finding, severity, exposed, criticality in findings:

    graph.add_node(
    finding,
    severity,
    exposed=exposed,
    criticality=criticality
)
if severity == "CRITICAL":
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
