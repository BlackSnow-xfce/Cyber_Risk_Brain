from dataclasses import replace

import pytest
from fastapi import HTTPException

import api_app
from application import (
    BusinessImpactReadinessService,
    FindingAssetBusinessContextResolution,
    FindingAssetBusinessContextResolutionStatus,
    FindingNotFoundError,
    FindingRiskPriorityService,
    FindingsConfigurationError,
    RiskAssessmentStatus,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.enterprise_context import (
    AssetBusinessContext,
    BusinessEnvironment,
    ServiceCriticality,
)
from tests.application.test_finding_risk_context import FINDING_ID, project
from tests.application.test_finding_technical_effect import _enrichment
from application.finding_technical_effect import FindingTechnicalEffectService


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
        "facts": [],
    }
    assert payload["business_impact_readiness"]["status"] == "UNAVAILABLE"
    assert payload["business_impact_readiness"]["finding_id"] == FINDING_ID
    assert payload["business_impact_readiness"]["completeness_status"] == "no_data"
    assert payload["business_impact_readiness"]["source_type"] == "business_impact_readiness"
    assert payload["business_impact_readiness"]["source_reference"] == (
        f"business-impact-readiness:unavailable:{FINDING_ID}"
    )
    assert "business_service" in payload["business_impact_readiness"]["missing_requirements"]
    assert payload["service_impact_profile"] == {
        "status": "NOT_FOUND", "canonical_asset_id": None,
        "business_service": None, "confidentiality_importance": None,
        "integrity_importance": None, "availability_importance": None,
        "source_reference": None,
    }
    assert payload["technical_effect"]["finding_id"] == FINDING_ID
    assert payload["technical_effect"]["source_type"] == "finding_technical_effect"
    assert payload["business_impact_classification_readiness"]["status"] == "UNAVAILABLE"
    assert "service_impact_profile" in payload["business_impact_classification_readiness"]["missing_requirements"]
    assert payload["business_impact_classification_readiness"]["source_type"] == "business_impact_classification_readiness"
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


def test_endpoint_preserves_complete_technical_effect_source_binding() -> None:
    context = project()
    technical = FindingTechnicalEffectService().project(_enrichment())
    technical = replace(
        technical,
        finding_id=FINDING_ID,
        effects=tuple(
            replace(effect, finding_id=FINDING_ID)
            for effect in technical.effects
        ),
        completeness=replace(
            technical.completeness,
            provenance=replace(
                technical.completeness.provenance,
                source_reference=f"finding-technical-effect:available:{FINDING_ID}",
            ),
        ),
    )
    payload = api_app.finding_risk_context(
        FINDING_ID,
        UseCase(replace(context, technical_effect=technical)),
    ).model_dump()["technical_effect"]["effects"][0]
    assert payload["cvss_version"] == "3.1"
    assert payload["cvss_vector"].startswith("CVSS:3.1/")
    assert payload["source_type"] == "nvd"
    assert payload["source_reference"] == "nvd:record"
    assert payload["observed_at"] is not None


def test_endpoint_preserves_ready_business_context_and_result_provenance() -> None:
    context = project()
    business_context = FindingAssetBusinessContextResolution(
        finding_id=FINDING_ID,
        status=FindingAssetBusinessContextResolutionStatus.RESOLVED,
        context=AssetBusinessContext(
            "asset-lab-metasploitable2-001", "Controlled Service",
            BusinessEnvironment.TEST, ServiceCriticality.LOW,
            "product-owner:controlled-business-context",
        ),
    )
    readiness = BusinessImpactReadinessService().evaluate(business_context)
    payload = api_app.finding_risk_context(
        FINDING_ID,
        UseCase(replace(
            context,
            business_context=business_context,
            business_impact_readiness=readiness,
        )),
    ).model_dump()

    assert payload["business_context"]["facts"] == payload["business_impact_readiness"]["facts"]
    assert payload["business_impact_readiness"]["finding_id"] == FINDING_ID
    assert payload["business_impact_readiness"]["completeness_status"] == "available"
    assert payload["business_impact_readiness"]["source_reference"] == (
        f"business-impact-readiness:ready:{FINDING_ID}"
    )
    assert all(
        fact["source_reference"] == "product-owner:controlled-business-context"
        for fact in payload["business_impact_readiness"]["facts"]
    )
    assert payload["business_impact"] is None


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
