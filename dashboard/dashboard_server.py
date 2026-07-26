from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from core.decision.models import AttackReasoning
from dashboard.dashboard_data import DashboardDataBuilder

app = FastAPI(title="PredatorAI Dashboard")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )


builder = DashboardDataBuilder()

# Temporäre Beispieldaten bis die API angebunden wird.
_demo_findings = [
    AttackReasoning(
        title="Critical Internet-facing Vulnerability",
        score=98,
        risk_level="Critical",
        asset="SRV-WEB-01",
        vendor="OpenSSH",
        product="OpenSSH",
        version="8.9p1",
        cve="CVE-2024-6387",
        reasons=[
            "Internet-facing asset",
            "Public exploit available",
            "High EPSS",
            "CISA KEV listed",
        ],
        recommendations=[
            "Apply vendor patch immediately",
            "Restrict external access",
            "Validate remediation",
        ],
        business_impact="Remote compromise of a critical business service.",
        technical_impact="Unauthenticated remote code execution may be possible.",
        internet_exposed=True,
        crown_jewel=True,
        public_exploit=True,
        known_exploited=True,
        high_epss=True,
        high_cvss=True,
    )
]


@app.get("/api/dashboard")
def dashboard() -> dict:
    return builder.build(_demo_findings)


@app.get("/")
def index():
    index_file = STATIC_DIR / "index.html"

    if index_file.exists():
        return FileResponse(index_file)

    return {
        "application": "PredatorAI Dashboard",
        "status": "running",
        "message": "Frontend not installed yet.",
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
    }