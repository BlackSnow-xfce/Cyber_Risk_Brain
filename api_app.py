from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from connectors.connector_manager import ConnectorManager
from core.mapper import finding_to_universal
from analysis.risk_engine import RiskEngine

app = FastAPI(
    title="Cyber Risk Brain"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

@app.get("/")
def root():
    return {
        "status": "Cyber Risk Brain Online"
    }


@app.get("/api/findings")
def get_findings():

    connector_manager = ConnectorManager()
    connector_manager.load_connectors()

    findings = []

    for connector in connector_manager.connectors:
        findings.extend(
            connector.get_findings()
        )

    risk_engine = RiskEngine()

    result = []

    for finding in findings:

        universal_finding = finding_to_universal(
            finding
        )

        business_risk = risk_engine.calculate_business_risk(
            finding.__dict__
        )

        risk_score = risk_engine.calculate_risk_score(
            finding.__dict__
        )

        reasons = risk_engine.explain_business_risk(
            finding.__dict__
        )

        recommendations = risk_engine.recommend_actions(
            finding.__dict__
        )

        result.append(
            {
                "source": universal_finding.source,
                "title": universal_finding.title,
                "vendor_severity": universal_finding.vendor_severity,
                "business_risk": business_risk,
                "risk_score": risk_score,
                "reasons": reasons,
                "recommendations": recommendations,
                "owner": finding.owner,
                "sla_days": finding.sla_days
            }
        )

    return result

@app.get("/api/team-risk")
def get_team_risk():

    findings = get_findings()

    risk_engine = RiskEngine()

    return risk_engine.calculate_team_risk(
        findings
    )