from __future__ import annotations

import pytest

from analysis.risk_engine import RiskEngine
from application import (
    AssetCriticality,
    RiskAssessmentInput,
    RiskAssessmentStatus,
    RiskInputState,
    RiskInputValue,
    RiskReadinessService,
)
from core.models import UniversalFinding


def _finding(vendor_severity: str = "Critical") -> UniversalFinding:
    return UniversalFinding(
        id="finding-1",
        source="scanner",
        title="Observed scanner finding",
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


def _complete_input(
    vendor_severity: str = "Critical",
) -> RiskAssessmentInput:
    return RiskAssessmentInput(
        finding_id="finding-1",
        finding_source="controlled-test",
        title="Controlled finding",
        vendor_severity=vendor_severity,
        asset="asset-1",
        business_criticality=RiskInputValue.authoritative(
            AssetCriticality.HIGH,
            "asset-context-test",
        ),
        exposure=RiskInputValue.authoritative(
            True,
            "exposure-test",
        ),
        detection_available=RiskInputValue.authoritative(
            True,
            "detection-test",
        ),
        threat_intelligence_match=RiskInputValue.authoritative(
            False,
            "threat-intelligence-test",
        ),
        mitre_tactic=RiskInputValue.authoritative(
            None,
            "mitre-test",
        ),
    )


class FailingRiskEngine:
    def calculate_risk_score(self, node: dict[str, object]) -> int:
        raise AssertionError("RiskEngine must not be called.")


class RecordingRiskEngine(RiskEngine):
    def __init__(self) -> None:
        super().__init__()
        self.nodes: list[dict[str, object]] = []

    def calculate_risk_score(self, node: dict[str, object]) -> int:
        self.nodes.append(node)
        return super().calculate_risk_score(node)


def test_universal_finding_without_context_is_not_assessed() -> None:
    assessment_input = RiskAssessmentInput.from_universal_finding(
        _finding()
    )
    result = RiskReadinessService(
        FailingRiskEngine()
    ).assess(assessment_input)

    assert result.status is RiskAssessmentStatus.INSUFFICIENT_CONTEXT
    assert result.score is None
    assert {
        item.name: item.state
        for item in result.missing_inputs
    } == {
        "business_criticality": RiskInputState.UNKNOWN,
        "exposure": RiskInputState.NOT_EVALUATED,
        "detection_available": RiskInputState.NOT_EVALUATED,
        "threat_intelligence_match": RiskInputState.NOT_EVALUATED,
        "mitre_tactic": RiskInputState.NOT_EVALUATED,
    }


def test_projection_does_not_reinterpret_legacy_finding_defaults() -> None:
    assessment_input = RiskAssessmentInput.from_universal_finding(
        _finding()
    )

    assert assessment_input.business_criticality.value is None
    assert assessment_input.exposure.value is None
    assert assessment_input.detection_available.value is None
    assert assessment_input.threat_intelligence_match.value is None
    assert assessment_input.mitre_tactic.value is None


def test_complete_authoritative_input_reuses_existing_risk_engine() -> None:
    risk_engine = RecordingRiskEngine()

    result = RiskReadinessService(risk_engine).assess(
        _complete_input()
    )

    assert result.status is RiskAssessmentStatus.ASSESSED
    assert result.score == 50
    assert risk_engine.nodes == [
        {
            "criticality": "HIGH",
            "exposed": True,
            "detection": True,
            "threat_intel": False,
            "mitre": None,
        }
    ]


def test_authoritative_required_input_cannot_have_missing_value() -> None:
    complete_input = _complete_input()

    with pytest.raises(
        ValueError,
        match="Authoritative exposure requires a value",
    ):
        RiskAssessmentInput(
            finding_id=complete_input.finding_id,
            finding_source=complete_input.finding_source,
            title=complete_input.title,
            vendor_severity=complete_input.vendor_severity,
            asset=complete_input.asset,
            business_criticality=complete_input.business_criticality,
            exposure=RiskInputValue.authoritative(
                None,
                "exposure-test",
            ),
            detection_available=complete_input.detection_available,
            threat_intelligence_match=(
                complete_input.threat_intelligence_match
            ),
            mitre_tactic=complete_input.mitre_tactic,
        )


def test_vendor_severity_does_not_change_risk_engine_input_or_score() -> None:
    first_engine = RecordingRiskEngine()
    second_engine = RecordingRiskEngine()

    first_result = RiskReadinessService(first_engine).assess(
        _complete_input("Critical")
    )
    second_result = RiskReadinessService(second_engine).assess(
        _complete_input("Low")
    )

    assert first_engine.nodes == second_engine.nodes
    assert first_result.score == second_result.score


def test_assessment_does_not_start_legacy_pipeline(monkeypatch) -> None:
    from core.predator_engine import PredatorEngine

    def fail_run(self) -> None:
        raise AssertionError("PredatorEngine.run() must not be called.")

    monkeypatch.setattr(PredatorEngine, "run", fail_run)

    result = RiskReadinessService(
        FailingRiskEngine()
    ).assess_finding(_finding())

    assert result.status is RiskAssessmentStatus.INSUFFICIENT_CONTEXT
