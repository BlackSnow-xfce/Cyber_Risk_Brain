import pytest

from core.decision.models import (
    AttackReasoning,
    BusinessImpact,
    Confidence,
    ConfidenceLevel,
    DecisionAction,
    DecisionPriority,
    DecisionResult,
    Recommendation,
)


def _create_decision_result(
    *,
    finding_id: str = "finding-1",
    decision: str = "Investigate the finding.",
    confidence_score: float = 50,
    recommendations: list[Recommendation] | None = None,
) -> DecisionResult:
    return DecisionResult(
        finding_id=finding_id,
        priority=DecisionPriority.HIGH,
        action=DecisionAction.INVESTIGATE,
        decision=decision,
        attack_reasoning=AttackReasoning(summary="Potential attack activity."),
        business_impact=BusinessImpact(summary="Potential business impact."),
        confidence=Confidence(
            score=confidence_score,
            level=ConfidenceLevel.MEDIUM,
        ),
        recommendations=recommendations or [],
    )


def test_decision_result_requires_identity_and_decision_text() -> None:
    with pytest.raises(ValueError, match="Finding ID must not be empty"):
        _create_decision_result(finding_id=" ")

    with pytest.raises(ValueError, match="Decision must not be empty"):
        _create_decision_result(decision=" ")


def test_decision_result_enforces_confidence_boundaries() -> None:
    assert _create_decision_result(confidence_score=0).confidence_score == 0
    assert _create_decision_result(confidence_score=100).confidence_score == 100

    with pytest.raises(ValueError, match="between 0 and 100"):
        _create_decision_result(confidence_score=-0.1)

    with pytest.raises(ValueError, match="between 0 and 100"):
        _create_decision_result(confidence_score=100.1)


def test_decision_result_sorts_recommendations_by_order() -> None:
    second = Recommendation(
        title="Second action",
        description="Perform second action.",
        action=DecisionAction.MONITOR,
        priority=DecisionPriority.MEDIUM,
        order=2,
    )
    first = Recommendation(
        title="First action",
        description="Perform first action.",
        action=DecisionAction.INVESTIGATE,
        priority=DecisionPriority.HIGH,
        order=1,
    )

    result = _create_decision_result(recommendations=[second, first])

    assert result.recommendations == [first, second]
