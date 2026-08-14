from datetime import datetime, timedelta, timezone

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
from core.explainability import DecisionExplainabilityProjectionBuilder


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


def test_projection_exposes_standardized_version_metadata() -> None:
    generated_at = datetime(2026, 8, 4, 12, 30, tzinfo=timezone.utc)
    projection = DecisionExplainabilityProjectionBuilder(
        generated_at=generated_at
    ).build(_create_decision_result())

    assert projection.projection_version == "1.0"
    assert projection.source_version == "1.0"
    assert projection.generated_at == generated_at
    assert projection.to_dict()["projectionVersion"] == "1.0"
    assert projection.to_dict()["sourceVersion"] == "1.0"
    assert projection.to_dict()["generatedAt"] == generated_at.isoformat()


def test_projection_requires_timezone_aware_utc_generation_time() -> None:
    generated_at = datetime(2026, 8, 4, 12, 30)

    with pytest.raises(ValueError, match="timezone-aware UTC"):
        DecisionExplainabilityProjectionBuilder(
            generated_at=generated_at
        ).build(_create_decision_result())


def test_projection_versioning_is_deterministic_and_backward_compatible() -> None:
    generated_at = datetime(2026, 8, 4, 12, 30, tzinfo=timezone.utc)
    builder = DecisionExplainabilityProjectionBuilder(
        generated_at=generated_at
    )

    first_projection = builder.build(_create_decision_result()).to_dict()
    second_projection = builder.build(_create_decision_result()).to_dict()
    default_projection = DecisionExplainabilityProjectionBuilder().build(
        _create_decision_result()
    )

    assert first_projection == second_projection
    assert default_projection.generated_at.utcoffset() == timedelta(0)
