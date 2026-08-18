import pytest
from fastapi import HTTPException

import api_app
from application import (
    FindingExplanationConfigurationError,
    FindingExplanationGenerationStatus,
    FindingExplanationInput,
    FindingExplanationInputBuilder,
    FindingExplanationModelRequest,
    FindingExplanationModelResponse,
    FindingExplanationResult,
    FindingExplanationService,
    FindingNotFoundError,
    FindingsConfigurationError,
    RiskAssessmentInput,
    RiskReadinessService,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.models import UniversalFinding


class StubUseCase:
    def __init__(
        self,
        result: FindingExplanationResult | BaseException,
    ) -> None:
        self.result = result
        self.calls: list[str] = []

    def explain(self, finding_id: str) -> FindingExplanationResult:
        self.calls.append(finding_id)
        if isinstance(self.result, BaseException):
            raise self.result
        return self.result


class ErrorModel:
    provider_id = "controlled-provider"
    model_id = "controlled-model"

    def __init__(self, error: BaseException) -> None:
        self.error = error

    def generate(
        self,
        request: FindingExplanationModelRequest,
    ) -> FindingExplanationModelResponse:
        raise self.error


class GeneratedModel:
    provider_id = "controlled-provider"
    model_id = "controlled-model"

    def generate(
        self,
        request: FindingExplanationModelRequest,
    ) -> FindingExplanationModelResponse:
        return FindingExplanationModelResponse(
            provider_id=self.provider_id,
            model_id=self.model_id,
            output={
                "summary": {
                    "kind": "CONTEXTUAL_INFERENCE",
                    "text": "The controlled finding is present.",
                    "basis_fact_ids": ["finding.title"],
                },
                "technical_reasoning": [
                    {
                        "kind": "GENERAL_SECURITY_REASONING",
                        "text": "General security context.",
                        "basis_fact_ids": [],
                    }
                ],
                "organizational_relevance": [],
                "uncertainty_statement": {
                    "kind": "CONTEXTUAL_INFERENCE",
                    "text": "Exposure was not evaluated.",
                    "basis_fact_ids": ["risk.exposure_state"],
                },
            },
        )


class ForbiddenRiskEngine:
    def calculate_risk_score(self, node: dict[str, object]) -> int:
        raise AssertionError("RiskEngine must not be called.")


def _input() -> FindingExplanationInput:
    finding = UniversalFinding(
        id="finding-controlled-001",
        source="greenbone",
        title="Controlled finding",
        vendor_severity="Medium",
        business_criticality="UNKNOWN",
        asset="192.0.2.10",
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
    )
    context = AssetContext(
        ObservedAssetIdentifier(
            AssetIdentifierType.IP_ADDRESS,
            finding.asset,
        ),
        "asset-controlled-001",
        AssetCriticality.LOW,
        "controlled-test:asset-classification",
    )
    risk_input = RiskAssessmentInput.from_universal_finding(
        finding
    ).with_asset_context(context)
    risk_result = RiskReadinessService(ForbiddenRiskEngine()).assess(
        risk_input
    )
    return FindingExplanationInputBuilder.build(
        finding,
        context,
        risk_input,
        risk_result,
    )


def _failed_result(
    error: BaseException,
) -> FindingExplanationResult:
    return FindingExplanationService(ErrorModel(error)).explain(_input())


def test_endpoint_projects_generated_result_and_calls_use_case_once() -> None:
    result = FindingExplanationService(GeneratedModel()).explain(_input())
    use_case = StubUseCase(result)

    response = api_app.explain_finding(
        "finding-controlled-001",
        use_case,
    )

    assert use_case.calls == ["finding-controlled-001"]
    projection = response.model_dump(mode="json")
    assert projection["generation_status"] == "GENERATED"
    assert projection["factual_context"] == [
        {
            "fact_id": fact.fact_id,
            "value": fact.value,
            "source_reference": fact.source_reference,
        }
        for fact in result.factual_context
    ]
    assert projection["missing_context"] == [
        {"name": item.name, "state": item.state.value}
        for item in result.missing_context
    ]
    assert projection["provider_id"] == "controlled-provider"
    assert projection["model_id"] == "controlled-model"
    assert projection["input_contract_version"] == "1.0"
    assert projection["input_digest"] == result.input_digest
    assert projection["used_fact_ids"] == [
        "finding.title",
        "risk.exposure_state",
    ]
    assert projection["model_output"] == {
        "summary": {
            "kind": "CONTEXTUAL_INFERENCE",
            "text": "The controlled finding is present.",
            "basis_fact_ids": ["finding.title"],
        },
        "technical_reasoning": [
            {
                "kind": "GENERAL_SECURITY_REASONING",
                "text": "General security context.",
                "basis_fact_ids": [],
            }
        ],
        "organizational_relevance": [],
        "uncertainty_statement": {
            "kind": "CONTEXTUAL_INFERENCE",
            "text": "Exposure was not evaluated.",
            "basis_fact_ids": ["risk.exposure_state"],
        },
    }


def test_endpoint_returns_not_found_for_unknown_finding() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.explain_finding(
            "unknown-finding",
            StubUseCase(FindingNotFoundError("unknown-finding")),
        )

    assert captured.value.status_code == 404
    assert captured.value.detail == "Finding was not found."


def test_endpoint_reports_missing_findings_configuration() -> None:
    error = FindingsConfigurationError(
        "GREENBONE_REPORT_PATH is not configured."
    )

    with pytest.raises(HTTPException) as captured:
        api_app.explain_finding("finding-controlled-001", StubUseCase(error))

    assert captured.value.status_code == 503
    assert captured.value.detail == str(error)


@pytest.mark.parametrize("error", [OSError("controlled"), ValueError("controlled")])
def test_endpoint_reports_invalid_or_unreadable_findings_source(
    error: BaseException,
) -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.explain_finding("finding-controlled-001", StubUseCase(error))

    assert captured.value.status_code == 500
    assert captured.value.detail == (
        "Configured finding context could not be loaded."
    )


def test_endpoint_transports_controlled_explanation_status() -> None:
    result = _failed_result(
        FindingExplanationConfigurationError("controlled")
    )

    response = api_app.explain_finding(
        "finding-controlled-001",
        StubUseCase(result),
    )

    assert response.generation_status == (
        FindingExplanationGenerationStatus.CONFIGURATION_ERROR.value
    )
    assert response.provider_id is None
    assert response.model_output is None
