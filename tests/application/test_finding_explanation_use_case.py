import api_app

from application import (
    FindingExplanationGenerationStatus,
    FindingExplanationModelRequest,
    FindingExplanationModelResponse,
    FindingExplanationService,
    FindingExplanationUseCase,
    FindingNotFoundError,
    RiskReadinessService,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.models import UniversalFinding


class StubFindings:
    def __init__(self, findings: list[UniversalFinding]) -> None:
        self._findings = findings

    def get_findings(self) -> list[UniversalFinding]:
        return self._findings


class StubAssetContexts:
    def __init__(self) -> None:
        self.calls: list[ObservedAssetIdentifier] = []

    def resolve(
        self,
        identifier: ObservedAssetIdentifier,
    ) -> AssetContext:
        self.calls.append(identifier)
        return AssetContext(
            observed_identifier=identifier,
            canonical_asset_id="asset-controlled-001",
            criticality=AssetCriticality.LOW,
            source_reference="controlled-test:asset-classification",
        )


class ForbiddenRiskEngine:
    def __init__(self) -> None:
        self.calls = 0

    def calculate_risk_score(self, node: dict[str, object]) -> int:
        self.calls += 1
        raise AssertionError("RiskEngine must not be called.")


class CountingModel:
    provider_id = "controlled-provider"
    model_id = "controlled-model"

    def __init__(self) -> None:
        self.calls = 0

    def generate(
        self,
        request: FindingExplanationModelRequest,
    ) -> FindingExplanationModelResponse:
        self.calls += 1
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


def _finding(asset: str = "192.0.2.10") -> UniversalFinding:
    return UniversalFinding(
        id="finding-controlled-001",
        source="greenbone",
        title="Controlled finding",
        vendor_severity="Medium",
        business_criticality="UNKNOWN",
        asset=asset,
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
    )


def test_use_case_reuses_explanation_once_without_risk_engine() -> None:
    model = CountingModel()
    risk_engine = ForbiddenRiskEngine()
    use_case = FindingExplanationUseCase(
        StubFindings([_finding()]),
        StubAssetContexts(),
        RiskReadinessService(risk_engine),
        FindingExplanationService(model),
    )

    result = use_case.explain("finding-controlled-001")

    assert result.generation_status is (
        FindingExplanationGenerationStatus.GENERATED
    )
    assert model.calls == 1
    assert risk_engine.calls == 0


def test_hostname_uses_unresolved_context_without_http_failure() -> None:
    model = CountingModel()
    asset_contexts = StubAssetContexts()
    use_case = FindingExplanationUseCase(
        StubFindings([_finding("scanner-host.example.test")]),
        asset_contexts,
        RiskReadinessService(ForbiddenRiskEngine()),
        FindingExplanationService(model),
    )

    response = api_app.explain_finding(
        "finding-controlled-001",
        use_case,
    )

    assert response.generation_status == "GENERATED"
    assert asset_contexts.calls == []
    assert "asset.canonical_id" not in {
        fact.fact_id for fact in response.factual_context
    }
    assert "business_criticality" in {
        item.name for item in response.missing_context
    }


def test_unclassifiable_identifier_uses_unresolved_context() -> None:
    model = CountingModel()
    asset_contexts = StubAssetContexts()
    result = FindingExplanationUseCase(
        StubFindings([_finding("not a supported identifier")]),
        asset_contexts,
        RiskReadinessService(ForbiddenRiskEngine()),
        FindingExplanationService(model),
    ).explain("finding-controlled-001")

    assert result.generation_status is (
        FindingExplanationGenerationStatus.GENERATED
    )
    assert asset_contexts.calls == []
    assert model.calls == 1


def test_use_case_rejects_unknown_finding_before_explanation() -> None:
    model = CountingModel()
    use_case = FindingExplanationUseCase(
        StubFindings([_finding()]),
        StubAssetContexts(),
        RiskReadinessService(ForbiddenRiskEngine()),
        FindingExplanationService(model),
    )

    try:
        use_case.explain("unknown-finding")
    except FindingNotFoundError:
        pass
    else:
        raise AssertionError("Unknown finding must be rejected.")

    assert model.calls == 0
