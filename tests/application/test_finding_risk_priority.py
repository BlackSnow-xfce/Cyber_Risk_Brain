from dataclasses import replace

import pytest

from application import (
    FindingRiskPriorityService,
    FindingRiskPriorityStatus,
    RiskAssessmentReadinessStatus,
    RiskAssessmentStatus,
)
from core.decision.models import DecisionPriority
from core.explainability import CompletenessStatus
from tests.application.test_finding_risk_context import FINDING_ID, project


class Classifier:
    def __init__(self, band: DecisionPriority = DecisionPriority.HIGH) -> None:
        self.band = band
        self.calls: list[int] = []

    def calculate(self, risk_score: int) -> DecisionPriority:
        self.calls.append(risk_score)
        return self.band


class ForbiddenClassifier:
    def calculate(self, risk_score: int) -> DecisionPriority:
        raise AssertionError("An unavailable priority must not be classified.")


def ready_inputs(score: int = 80):
    context = project()
    assessment = replace(
        context.assessment,
        status=RiskAssessmentStatus.ASSESSED,
        missing_inputs=(),
        score=score,
    )
    assert (
        context.evidence_readiness.status
        is RiskAssessmentReadinessStatus.READY
    )
    return assessment, context.evidence_readiness


def test_prioritized_result_retains_score_evidence_and_provenance() -> None:
    assessment, evidence_readiness = ready_inputs(80)
    classifier = Classifier()

    result = FindingRiskPriorityService(classifier).prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    assert classifier.calls == [80]
    assert result.status is FindingRiskPriorityStatus.PRIORITIZED
    assert result.band is DecisionPriority.HIGH
    assert result.score == 80
    assert result.considered_evidence_ids == (
        evidence_readiness.considered_evidence_ids
    )
    assert result.referenced_input_references[: len(
        evidence_readiness.referenced_input_references
    )] == evidence_readiness.referenced_input_references
    assert "greenbone" in result.referenced_input_references
    assert (
        "product-owner:metasploitable2-lab-classification"
        in result.referenced_input_references
    )
    assert result.missing_requirements == ()
    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.completeness.provenance.source_reference.endswith(FINDING_ID)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0, DecisionPriority.INFORMATIONAL),
        (24, DecisionPriority.INFORMATIONAL),
        (25, DecisionPriority.LOW),
        (49, DecisionPriority.LOW),
        (50, DecisionPriority.MEDIUM),
        (74, DecisionPriority.MEDIUM),
        (75, DecisionPriority.HIGH),
        (89, DecisionPriority.HIGH),
        (90, DecisionPriority.CRITICAL),
        (100, DecisionPriority.CRITICAL),
    ],
)
def test_existing_priority_policy_classifies_boundary_scores(score, expected) -> None:
    assessment, evidence_readiness = ready_inputs(score)

    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    assert result.band is expected


def test_missing_context_refuses_priority_without_using_technical_signals() -> None:
    context = project()

    result = FindingRiskPriorityService(ForbiddenClassifier()).prioritize(
        FINDING_ID,
        context.assessment,
        context.evidence_readiness,
    )

    assert context.source_facts
    assert context.threat_intelligence.relationships
    assert result.status is FindingRiskPriorityStatus.UNAVAILABLE
    assert result.band is result.score is None
    assert "risk_assessment:INSUFFICIENT_CONTEXT" in result.missing_requirements
    assert any(
        requirement.startswith("risk_input:")
        for requirement in result.missing_requirements
    )


def test_insufficient_evidence_refuses_an_assessed_score() -> None:
    assessment, evidence_readiness = ready_inputs(95)
    insufficient = replace(
        evidence_readiness,
        status=RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE,
        missing_requirements=("correlation_derived_evidence",),
    )

    result = FindingRiskPriorityService(ForbiddenClassifier()).prioritize(
        FINDING_ID,
        assessment,
        insufficient,
    )

    assert result.status is FindingRiskPriorityStatus.UNAVAILABLE
    assert result.band is result.score is None
    assert result.missing_requirements == (
        "correlation_derived_evidence",
        "evidence_readiness:INSUFFICIENT_EVIDENCE",
    )


def test_ready_evidence_with_missing_requirements_fails_closed() -> None:
    assessment, evidence_readiness = ready_inputs(80)
    inconsistent = replace(
        evidence_readiness,
        missing_requirements=("remaining_authoritative_evidence",),
    )
    classifier = Classifier()

    result = FindingRiskPriorityService(classifier).prioritize(
        FINDING_ID,
        assessment,
        inconsistent,
    )

    assert classifier.calls == []
    assert result.status is FindingRiskPriorityStatus.UNAVAILABLE
    assert result.band is result.score is None
    assert result.missing_requirements == (
        "remaining_authoritative_evidence",
    )
    assert "remaining_authoritative_evidence" in result.reason


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("band", DecisionPriority.HIGH, "band or score"),
        ("score", 80, "band or score"),
    ],
)
def test_unavailable_result_rejects_priority_values(
    field, value, message
) -> None:
    context = project()
    result = FindingRiskPriorityService(ForbiddenClassifier()).prioritize(
        FINDING_ID,
        context.assessment,
        context.evidence_readiness,
    )

    with pytest.raises(ValueError, match=message):
        replace(result, **{field: value})


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("band", None, "DecisionPriority band"),
        ("score", None, "authoritative score"),
        (
            "missing_requirements",
            ("remaining_context",),
            "missing requirements",
        ),
    ],
)
def test_prioritized_result_rejects_incomplete_state(
    field, value, message
) -> None:
    assessment, evidence_readiness = ready_inputs(80)
    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    with pytest.raises(ValueError, match=message):
        replace(result, **{field: value})


def test_prioritized_result_rejects_missing_provenance() -> None:
    assessment, evidence_readiness = ready_inputs(80)
    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    with pytest.raises(ValueError, match="evidence and input provenance"):
        replace(result, considered_evidence_ids=())


@pytest.mark.parametrize(
    "band",
    [
        "invented",
        DecisionPriority.HIGH.value,
        1,
        object(),
    ],
)
def test_prioritized_result_rejects_non_enum_band(band) -> None:
    assessment, evidence_readiness = ready_inputs(80)
    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    with pytest.raises(ValueError, match="DecisionPriority band"):
        replace(result, band=band)


@pytest.mark.parametrize("score", [80.5, 80.0, True, False, -1, 101])
def test_prioritized_result_rejects_invalid_score_runtime_value(score) -> None:
    assessment, evidence_readiness = ready_inputs(80)
    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    with pytest.raises(ValueError, match="bounded authoritative score"):
        replace(result, score=score)


@pytest.mark.parametrize("score", [0, 1, 50, 80, 100])
def test_prioritized_result_accepts_authoritative_integer_score(score) -> None:
    assessment, evidence_readiness = ready_inputs(score)

    result = FindingRiskPriorityService().prioritize(
        FINDING_ID,
        assessment,
        evidence_readiness,
    )

    assert isinstance(result.band, DecisionPriority)
    assert type(result.score) is int
    assert result.score == score


def test_unavailable_result_requires_truthful_reason() -> None:
    context = project()
    result = FindingRiskPriorityService(ForbiddenClassifier()).prioritize(
        FINDING_ID,
        context.assessment,
        context.evidence_readiness,
    )

    with pytest.raises(ValueError, match="truthful reason"):
        replace(result, reason=" ")


@pytest.mark.parametrize("source", ["assessment", "evidence"])
def test_mismatched_finding_identity_fails_closed(source) -> None:
    assessment, evidence_readiness = ready_inputs()
    if source == "assessment":
        assessment = replace(assessment, finding_id="different")
    else:
        evidence_readiness = replace(
            evidence_readiness,
            finding_id="different",
        )

    with pytest.raises(ValueError, match="different findings"):
        FindingRiskPriorityService().prioritize(
            FINDING_ID,
            assessment,
            evidence_readiness,
        )


@pytest.mark.parametrize("score", [None, -1, 101, True])
def test_invalid_assessed_score_fails_closed(score) -> None:
    assessment, evidence_readiness = ready_inputs()
    assessment = replace(assessment, score=score)

    with pytest.raises(ValueError, match="bounded score"):
        FindingRiskPriorityService().prioritize(
            FINDING_ID,
            assessment,
            evidence_readiness,
        )


@pytest.mark.parametrize("missing", ["evidence", "references", "completeness"])
def test_ready_evidence_requires_identifiers_and_provenance(missing) -> None:
    assessment, evidence_readiness = ready_inputs()
    if missing == "evidence":
        evidence_readiness = replace(
            evidence_readiness,
            considered_evidence_ids=(),
        )
    elif missing == "references":
        evidence_readiness = replace(
            evidence_readiness,
            referenced_input_references=(),
        )
    else:
        evidence_readiness = replace(
            evidence_readiness,
            completeness=replace(
                evidence_readiness.completeness,
                status=CompletenessStatus.NO_DATA,
            ),
        )

    with pytest.raises(ValueError, match="identifiers and provenance"):
        FindingRiskPriorityService().prioritize(
            FINDING_ID,
            assessment,
            evidence_readiness,
        )
