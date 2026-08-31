from dataclasses import replace

import pytest
from fastapi import HTTPException

import api_app
from application import (
    FindingNotFoundError,
    FindingRiskPriorityService,
    FindingsConfigurationError,
    RiskAssessmentStatus,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from tests.application.test_finding_risk_context import FINDING_ID, project


class UseCase:
    def __init__(self, result) -> None:
        self.result = result

    def project(self, finding_id: str):
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_endpoint_transports_typed_provenance_evidence_and_fail_closed_result() -> None:
    response = api_app.finding_risk_context(FINDING_ID, UseCase(project()))
    payload = response.model_dump()

    assert payload["finding_id"] == FINDING_ID
    assert payload["asset_context"] == {
        "status": "resolved",
        "observed_identifier_type": "ip_address",
        "observed_identifier_value": "172.18.0.19",
        "canonical_asset_id": "asset-lab-metasploitable2-001",
        "criticality": "LOW",
        "source_reference": "product-owner:metasploitable2-lab-classification",
    }
    relationship = payload["threat_intelligence"]["relationships"][0]
    assert relationship["applicability"] == "applicable"
    assert relationship["cve_identifier"] == "CVE-2004-2687"
    assert relationship["intelligence"]["nvd"]["provenance"] == {
        "source_type": "nvd",
        "source_reference": "nvd:CVE-2004-2687",
    }
    evidence = payload["evidence"][0]
    assert evidence["kind"] == "derived"
    assert evidence["evidence_type"] == "correlation"
    assert evidence["input_references"] == payload[
        "evidence_readiness"
    ]["referenced_input_references"]
    assert {item["name"] for item in payload["risk_inputs"]} == {
        "business_criticality",
        "exposure",
        "detection_available",
        "threat_intelligence_match",
        "mitre_tactic",
    }
    assert payload["assessment"]["status"] == "INSUFFICIENT_CONTEXT"
    assert payload["assessment"]["score"] is None
    assert payload["priority"]["status"] == "UNAVAILABLE"
    assert payload["priority"]["band"] is None
    assert payload["priority"]["score"] is None
    assert payload["priority"]["considered_evidence_ids"] == [
        evidence["identifier"]
    ]
    assert payload["priority"]["referenced_input_references"][: len(
        evidence["input_references"]
    )] == evidence["input_references"]
    assert "greenbone" in payload["priority"]["referenced_input_references"]
    assert payload["priority"]["missing_requirements"]
    assert payload["priority"]["source_type"] == "finding_risk_priority"
    assert payload["business_impact"] is None
    assert payload["business_context"] == {
        "status": "NOT_FOUND",
        "canonical_asset_id": None,
        "business_service": None,
        "environment": None,
        "service_criticality": None,
        "source_reference": None,
    }
    assert payload["business_impact_readiness"]["status"] == "UNAVAILABLE"
    assert "business_service" in payload["business_impact_readiness"]["missing_requirements"]
    assert payload["decision"] is None
    assert payload["recommendations"] == []


def test_endpoint_transports_explainable_gated_priority() -> None:
    context = project()
    assessment = replace(
        context.assessment,
        status=RiskAssessmentStatus.ASSESSED,
        missing_inputs=(),
        score=80,
    )
    priority = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        context.evidence_readiness,
    )

    response = api_app.finding_risk_context(
        FINDING_ID,
        UseCase(replace(context, assessment=assessment, priority=priority)),
    )
    payload = response.model_dump()["priority"]

    assert payload["status"] == "PRIORITIZED"
    assert payload["band"] == "high"
    assert payload["score"] == 80
    assert payload["considered_evidence_ids"]
    assert payload["referenced_input_references"]
    assert payload["missing_requirements"] == []
    assert payload["source_reference"] == (
        f"finding-risk-priority:prioritized:{FINDING_ID}"
    )


@pytest.mark.parametrize(
    ("error", "status"),
    [
        (FindingNotFoundError("missing"), 404),
        (FindingsConfigurationError("not configured"), 503),
        (ThreatIntelligenceSourceUnavailableError("unavailable"), 503),
        (ThreatIntelligenceTimeoutError("timeout"), 504),
        (ThreatIntelligenceInvalidResponseError("invalid"), 502),
        (ValueError("source integrity failure"), 500),
    ],
)
def test_endpoint_preserves_controlled_failure_states(error, status) -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.finding_risk_context(FINDING_ID, UseCase(error))

    assert captured.value.status_code == status
