from copy import deepcopy

from core.decision.models import (
    AttackReasoning,
    BusinessImpact,
    Confidence,
    ConfidenceLevel,
    DecisionAction,
    DecisionPriority,
    DecisionResult,
)
from core.explainability import (
    DecisionExplainabilityProjectionBuilder,
    DecisionTrace,
    DecisionTraceBuilder,
)


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


def test_projection_builder_reuses_existing_decision_trace_contract() -> None:
    projection = DecisionExplainabilityProjectionBuilder().build(
        _create_decision_result()
    )

    assert DecisionTraceBuilder is DecisionExplainabilityProjectionBuilder
    assert isinstance(projection, DecisionTrace)


def test_projection_builder_is_deterministic_and_preserves_source() -> None:
    result = _create_decision_result()
    original_result = deepcopy(result.to_dict())
    builder = DecisionExplainabilityProjectionBuilder()

    first_projection = builder.build(result).to_dict()
    second_projection = builder.build(result).to_dict()

    assert first_projection == second_projection
    assert result.to_dict() == original_result


def test_projection_builder_does_not_create_missing_optional_facts() -> None:
    projection = DecisionExplainabilityProjectionBuilder().build(
        _create_decision_result()
    )

    assert tuple(item.identifier for item in projection.items) == (
        "decision.summary",
        "attack_reasoning.summary",
        "business_impact.summary",
        "confidence.summary",
    )
