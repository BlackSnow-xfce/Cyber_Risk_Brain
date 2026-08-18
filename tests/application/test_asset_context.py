from __future__ import annotations

import json
from pathlib import Path

import pytest

from application import (
    AssetContextConfigurationError,
    AssetContextDataError,
    AssetContextQueryService,
    RiskAssessmentInput,
    RiskAssessmentStatus,
    RiskInputState,
    RiskReadinessService,
)
from core.enterprise_context import (
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.models import UniversalFinding


def _record(
    *,
    identifier: str = "192.0.2.10",
    canonical_asset_id: str = "asset-test-001",
    criticality: str = "HIGH",
    source_reference: str = "controlled-test:asset-context",
) -> dict[str, str]:
    return {
        "identifierType": "ip_address",
        "identifier": identifier,
        "canonicalAssetId": canonical_asset_id,
        "assetCriticality": criticality,
        "sourceReference": source_reference,
    }


def _source_service(
    monkeypatch: pytest.MonkeyPatch,
    records: list[dict[str, str]],
) -> AssetContextQueryService:
    source_text = json.dumps({"assets": records})
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding: source_text,
    )
    return AssetContextQueryService("controlled-assets.json")


def _source_text_service(
    monkeypatch: pytest.MonkeyPatch,
    source_text: str,
) -> AssetContextQueryService:
    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, encoding: source_text,
    )
    return AssetContextQueryService("controlled-assets.json")


def _identifier(value: str = "192.0.2.10") -> ObservedAssetIdentifier:
    return ObservedAssetIdentifier(
        identifier_type=AssetIdentifierType.IP_ADDRESS,
        value=value,
    )


def _finding(vendor_severity: str = "Critical") -> UniversalFinding:
    return UniversalFinding(
        id="finding-asset-context",
        source="scanner",
        title="Controlled scanner finding",
        vendor_severity=vendor_severity,
        business_criticality="UNKNOWN",
        asset="192.0.2.10",
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
    )


class FailingRiskEngine:
    def __init__(self) -> None:
        self.calls = 0

    def calculate_risk_score(self, node: dict[str, object]) -> int:
        self.calls += 1
        raise AssertionError("RiskEngine must not be called.")


def test_resolves_explicit_identifier_to_canonical_asset_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _source_service(monkeypatch, [_record()]).resolve(_identifier())

    assert context is not None
    assert context.observed_identifier == _identifier()
    assert context.canonical_asset_id == "asset-test-001"
    assert context.criticality is AssetCriticality.HIGH
    assert context.source_reference == "controlled-test:asset-context"
    assert context.canonical_asset_id != context.observed_identifier.value


def test_unknown_identifier_returns_no_context_without_low_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _source_service(monkeypatch, [_record()]).resolve(
        _identifier("198.51.100.20")
    )
    assessment_input = RiskAssessmentInput.from_universal_finding(
        _finding()
    ).with_asset_context(context)

    assert context is None
    assert assessment_input.business_criticality.state is RiskInputState.UNKNOWN
    assert assessment_input.business_criticality.value is None


def test_ambiguous_identifier_fails_without_heuristic_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _source_service(
        monkeypatch,
        [
            _record(canonical_asset_id="asset-test-001"),
            _record(canonical_asset_id="asset-test-002"),
        ],
    )

    with pytest.raises(AssetContextDataError, match="ambiguous"):
        service.resolve(_identifier())


@pytest.mark.parametrize(
    "document",
    [
        "not json",
        json.dumps({"records": []}),
        json.dumps({"assets": [{"identifier": "192.0.2.10"}]}),
        json.dumps({"assets": [_record(criticality="UNKNOWN")]}),
        json.dumps({"assets": [_record(identifier="not-an-ip")]}),
    ],
)
def test_invalid_asset_context_source_fails_controlled(
    monkeypatch: pytest.MonkeyPatch,
    document: str,
) -> None:
    with pytest.raises(AssetContextDataError):
        _source_text_service(monkeypatch, document).resolve(_identifier())


@pytest.mark.parametrize("context_path", [None, "", "  "])
def test_missing_asset_context_configuration_fails_controlled(
    context_path: str | None,
) -> None:
    with pytest.raises(
        AssetContextConfigurationError,
        match="ASSET_CONTEXT_PATH",
    ):
        AssetContextQueryService(context_path).resolve(_identifier())


def test_missing_asset_context_file_fails_controlled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_read(self: Path, encoding: str) -> str:
        raise FileNotFoundError("controlled missing source")

    monkeypatch.setattr(Path, "read_text", fail_read)

    with pytest.raises(
        AssetContextConfigurationError,
        match="cannot be read",
    ):
        AssetContextQueryService("missing-assets.json").resolve(_identifier())


def test_asset_context_projects_only_authoritative_criticality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _source_service(
        monkeypatch,
        [_record(criticality="LOW")],
    ).resolve(_identifier())

    assessment_input = RiskAssessmentInput.from_universal_finding(
        _finding("Critical")
    ).with_asset_context(context)

    assert assessment_input.vendor_severity == "Critical"
    assert assessment_input.business_criticality.state is (
        RiskInputState.AUTHORITATIVE
    )
    assert assessment_input.business_criticality.value is AssetCriticality.LOW
    assert assessment_input.business_criticality.source == (
        "controlled-test:asset-context"
    )
    assert assessment_input.exposure.state is RiskInputState.NOT_EVALUATED
    assert assessment_input.detection_available.state is (
        RiskInputState.NOT_EVALUATED
    )
    assert assessment_input.threat_intelligence_match.state is (
        RiskInputState.NOT_EVALUATED
    )
    assert assessment_input.mitre_tactic.state is RiskInputState.NOT_EVALUATED


def test_resolved_asset_context_remains_insufficient_for_risk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _source_service(
        monkeypatch,
        [_record(criticality="LOW")],
    ).resolve(_identifier())
    assessment_input = RiskAssessmentInput.from_universal_finding(
        _finding()
    ).with_asset_context(context)
    risk_engine = FailingRiskEngine()

    result = RiskReadinessService(risk_engine).assess(assessment_input)

    assert result.status is RiskAssessmentStatus.INSUFFICIENT_CONTEXT
    assert result.score is None
    assert risk_engine.calls == 0
    assert {item.name for item in result.missing_inputs} == {
        "exposure",
        "detection_available",
        "threat_intelligence_match",
        "mitre_tactic",
    }


def test_rejects_asset_context_for_different_observed_identifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    context = _source_service(
        monkeypatch,
        [_record(identifier="198.51.100.20")],
    ).resolve(
        _identifier("198.51.100.20")
    )

    with pytest.raises(ValueError, match="does not match"):
        RiskAssessmentInput.from_universal_finding(
            _finding()
        ).with_asset_context(context)
