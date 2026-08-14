from copy import deepcopy
from dataclasses import FrozenInstanceError

import pytest

from core.decision.models import (
    AttackReasoning,
    BusinessImpact,
    Confidence,
    ConfidenceLevel,
    DecisionAction,
    DecisionPriority,
    DecisionResult,
)
from core.explainability import DecisionTraceBuilder


def _create_decision_result() -> DecisionResult:
    return DecisionResult(
        finding_id="finding-1",
        priority=DecisionPriority.HIGH,
        action=DecisionAction.INVESTIGATE,
        decision="Investigate the finding.",
        attack_reasoning=AttackReasoning(summary="Potential attack activity."),
        business_impact=BusinessImpact(summary="Potential business impact."),
        confidence=Confidence(
            score=50,
            level=ConfidenceLevel.MEDIUM,
        ),
    )


def test_explainability_projection_is_read_only() -> None:
    projection = DecisionTraceBuilder().build(_create_decision_result())

    with pytest.raises(FrozenInstanceError):
        projection.decision = "Changed decision."


def test_explainability_projection_does_not_change_decision_result() -> None:
    result = _create_decision_result()
    original_result = deepcopy(result.to_dict())

    DecisionTraceBuilder().build(result)

    assert result.to_dict() == original_result


def test_explainability_projection_does_not_create_missing_facts() -> None:
    projection = DecisionTraceBuilder().build(_create_decision_result())

    assert tuple(item.identifier for item in projection.items) == (
        "decision.summary",
        "attack_reasoning.summary",
        "business_impact.summary",
        "confidence.summary",
    )
