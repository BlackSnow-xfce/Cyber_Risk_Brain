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
    Evidence,
    EvidenceType,
    Recommendation,
)
from core.explainability import (
    DecisionExplainabilityProjectionBuilder,
    ExplanationCategory,
    ExplanationItem,
    ExplanationProvenance,
)


def _create_decision_result() -> DecisionResult:
    return DecisionResult(
        finding_id="finding-1",
        priority=DecisionPriority.HIGH,
        action=DecisionAction.INVESTIGATE,
        decision="Investigate the finding.",
        attack_reasoning=AttackReasoning(
            summary="Potential attack activity.",
            attack_vector="External exposure.",
        ),
        business_impact=BusinessImpact(
            summary="Potential business impact.",
            business_service="Customer portal.",
        ),
        confidence=Confidence(
            score=50,
            level=ConfidenceLevel.MEDIUM,
            reasons=["Evidence is incomplete."],
            missing_information=["Asset ownership."],
        ),
        evidence=[
            Evidence(
                evidence_type=EvidenceType.FINDING,
                key="finding-status",
                value="open",
            )
        ],
        recommendations=[
            Recommendation(
                title="Investigate",
                description="Validate the finding.",
                action=DecisionAction.INVESTIGATE,
                priority=DecisionPriority.HIGH,
                order=1,
            )
        ],
    )


def test_provenance_is_read_only_and_item_construction_stays_compatible() -> None:
    provenance = ExplanationProvenance(
        source_type="decision_result",
        source_reference="decision",
    )
    item = ExplanationItem(
        identifier="decision.summary",
        category=ExplanationCategory.DECISION,
        title="Decision",
        description="Investigate the finding.",
        sequence=1,
    )

    with pytest.raises(FrozenInstanceError):
        provenance.source_reference = "confidence"

    assert item.provenance is None


def test_builder_adds_complete_provenance_from_existing_sources() -> None:
    projection = DecisionExplainabilityProjectionBuilder().build(
        _create_decision_result()
    )

    assert all(item.provenance is not None for item in projection.items)
    assert {
        item.provenance.source_reference
        for item in projection.items
        if item.provenance is not None
    } == {
        "decision",
        "attack_reasoning.summary",
        "attack_reasoning.attack_vector",
        "business_impact.summary",
        "business_impact.business_service",
        "confidence",
        "confidence.reasons[0]",
        "confidence.missing_information[0]",
        "evidence[0]",
        "recommendations[0]",
    }


def test_provenance_is_deterministic_and_contains_only_references() -> None:
    builder = DecisionExplainabilityProjectionBuilder()

    first_projection = builder.build(_create_decision_result()).to_dict()
    second_projection = builder.build(_create_decision_result()).to_dict()
    provenance_values = [
        item["provenance"]
        for item in first_projection["items"]
    ]

    assert first_projection == second_projection
    assert all(
        set(provenance) == {"sourceType", "sourceReference"}
        and provenance["sourceType"] == "decision_result"
        for provenance in provenance_values
    )
