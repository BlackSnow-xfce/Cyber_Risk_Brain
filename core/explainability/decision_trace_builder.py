from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.decision.models import (
    BusinessImpact,
    Confidence,
    DecisionResult,
    Evidence,
    Recommendation,
)
from core.explainability.decision_trace import DecisionTrace
from core.explainability.explanation_item import (
    ExplanationCategory,
    ExplanationItem,
    ExplanationProvenance,
)


class DecisionExplainabilityProjectionBuilder:
    """
    Builds a DecisionTrace from a canonical DecisionResult.

    This builder performs structural transformation only.

    It must not:

    - calculate risk
    - change priority
    - change the selected action
    - modify confidence
    - create new recommendations
    - reinterpret domain decisions
    """

    def __init__(self, *, generated_at: datetime | None = None) -> None:
        self._generated_at = generated_at

    def build(self, result: DecisionResult) -> DecisionTrace:
        if self._generated_at is None:
            self._generated_at = datetime.now(timezone.utc)

        items: list[ExplanationItem] = []
        sequence = 1

        items.append(
            ExplanationItem(
                identifier="decision.summary",
                category=ExplanationCategory.DECISION,
                title="Decision",
                description=result.decision,
                sequence=sequence,
                source="decision_engine",
                importance=1.0,
                provenance=self._provenance("decision"),
                metadata={
                    "priority": result.priority.value,
                    "action": result.action.value,
                    "requires_immediate_action": (
                        result.requires_immediate_action
                    ),
                },
            )
        )
        sequence += 1

        attack_items, sequence = self._build_attack_reasoning_items(
            result=result,
            start_sequence=sequence,
        )
        items.extend(attack_items)

        business_items, sequence = self._build_business_impact_items(
            business_impact=result.business_impact,
            start_sequence=sequence,
        )
        items.extend(business_items)

        confidence_items, sequence = self._build_confidence_items(
            confidence=result.confidence,
            start_sequence=sequence,
        )
        items.extend(confidence_items)

        evidence_items, sequence = self._build_evidence_items(
            evidence=result.evidence,
            start_sequence=sequence,
        )
        items.extend(evidence_items)

        recommendation_items, sequence = self._build_recommendation_items(
            recommendations=result.recommendations,
            start_sequence=sequence,
        )
        items.extend(recommendation_items)

        return DecisionTrace(
            finding_id=result.finding_id,
            decision=result.decision,
            priority=result.priority,
            action=result.action,
            confidence_score=result.confidence.score,
            confidence_level=result.confidence.level,
            items=tuple(items),
            metadata=dict(result.metadata),
            generated_at=self._generated_at,
        )

    def _build_attack_reasoning_items(
        self,
        result: DecisionResult,
        start_sequence: int,
    ) -> tuple[list[ExplanationItem], int]:
        reasoning = result.attack_reasoning
        items: list[ExplanationItem] = []
        sequence = start_sequence

        items.append(
            ExplanationItem(
                identifier="attack_reasoning.summary",
                category=ExplanationCategory.ATTACK_REASONING,
                title="Attack reasoning",
                description=reasoning.summary,
                sequence=sequence,
                source="decision_engine",
                importance=1.0,
                provenance=self._provenance("attack_reasoning.summary"),
            )
        )
        sequence += 1

        if reasoning.attack_vector:
            items.append(
                ExplanationItem(
                    identifier="attack_reasoning.attack_vector",
                    category=ExplanationCategory.ATTACK_REASONING,
                    title="Attack vector",
                    description=reasoning.attack_vector,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.9,
                    provenance=self._provenance(
                        "attack_reasoning.attack_vector"
                    ),
                )
            )
            sequence += 1

        if reasoning.exploitation_probability:
            items.append(
                ExplanationItem(
                    identifier="attack_reasoning.exploitation_probability",
                    category=ExplanationCategory.ATTACK_REASONING,
                    title="Exploitation probability",
                    description=reasoning.exploitation_probability,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.9,
                    provenance=self._provenance(
                        "attack_reasoning.exploitation_probability"
                    ),
                )
            )
            sequence += 1

        for index, outcome in enumerate(
            reasoning.likely_outcomes,
            start=1,
        ):
            if not outcome.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"attack_reasoning.outcome.{index}",
                    category=ExplanationCategory.ATTACK_REASONING,
                    title=f"Likely outcome {index}",
                    description=outcome,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.85,
                    provenance=self._provenance(
                        f"attack_reasoning.likely_outcomes[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        for index, attack_step in enumerate(
            reasoning.attack_steps,
            start=1,
        ):
            if not attack_step.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"attack_reasoning.step.{index}",
                    category=ExplanationCategory.ATTACK_REASONING,
                    title=f"Attack step {index}",
                    description=attack_step,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.8,
                    provenance=self._provenance(
                        f"attack_reasoning.attack_steps[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        for index, factor in enumerate(
            reasoning.supporting_factors,
            start=1,
        ):
            if not factor.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"attack_reasoning.supporting_factor.{index}",
                    category=ExplanationCategory.ATTACK_REASONING,
                    title=f"Supporting factor {index}",
                    description=factor,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.75,
                    provenance=self._provenance(
                        f"attack_reasoning.supporting_factors[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        for index, factor in enumerate(
            reasoning.limiting_factors,
            start=1,
        ):
            if not factor.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"attack_reasoning.limiting_factor.{index}",
                    category=ExplanationCategory.LIMITATION,
                    title=f"Limiting factor {index}",
                    description=factor,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.7,
                    provenance=self._provenance(
                        f"attack_reasoning.limiting_factors[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        return items, sequence

    def _build_business_impact_items(
        self,
        business_impact: BusinessImpact,
        start_sequence: int,
    ) -> tuple[list[ExplanationItem], int]:
        items: list[ExplanationItem] = []
        sequence = start_sequence

        items.append(
            ExplanationItem(
                identifier="business_impact.summary",
                category=ExplanationCategory.BUSINESS_IMPACT,
                title="Business impact",
                description=business_impact.summary,
                sequence=sequence,
                source="decision_engine",
                importance=1.0,
                provenance=self._provenance("business_impact.summary"),
            )
        )
        sequence += 1

        impact_fields: tuple[tuple[str, str, str, str | None], ...] = (
            (
                "business_service",
                "Business service",
                "business_impact.business_service",
                business_impact.business_service,
            ),
            (
                "asset_criticality",
                "Asset criticality",
                "business_impact.asset_criticality",
                business_impact.asset_criticality,
            ),
            (
                "confidentiality",
                "Confidentiality impact",
                "business_impact.confidentiality_impact",
                business_impact.confidentiality_impact,
            ),
            (
                "integrity",
                "Integrity impact",
                "business_impact.integrity_impact",
                business_impact.integrity_impact,
            ),
            (
                "availability",
                "Availability impact",
                "business_impact.availability_impact",
                business_impact.availability_impact,
            ),
            (
                "financial",
                "Financial impact",
                "business_impact.financial_impact",
                business_impact.financial_impact,
            ),
            (
                "operational",
                "Operational impact",
                "business_impact.operational_impact",
                business_impact.operational_impact,
            ),
            (
                "regulatory",
                "Regulatory impact",
                "business_impact.regulatory_impact",
                business_impact.regulatory_impact,
            ),
            (
                "reputational",
                "Reputational impact",
                "business_impact.reputational_impact",
                business_impact.reputational_impact,
            ),
        )

        for identifier, title, source_reference, description in impact_fields:
            if description is None or not description.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"business_impact.{identifier}",
                    category=ExplanationCategory.BUSINESS_IMPACT,
                    title=title,
                    description=description,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.8,
                    provenance=self._provenance(source_reference),
                )
            )
            sequence += 1

        for index, process in enumerate(
            business_impact.affected_processes,
            start=1,
        ):
            if not process.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"business_impact.affected_process.{index}",
                    category=ExplanationCategory.BUSINESS_IMPACT,
                    title=f"Affected process {index}",
                    description=process,
                    sequence=sequence,
                    source="decision_engine",
                    importance=0.75,
                    provenance=self._provenance(
                        f"business_impact.affected_processes[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        return items, sequence

    def _build_confidence_items(
        self,
        confidence: Confidence,
        start_sequence: int,
    ) -> tuple[list[ExplanationItem], int]:
        items: list[ExplanationItem] = []
        sequence = start_sequence

        items.append(
            ExplanationItem(
                identifier="confidence.summary",
                category=ExplanationCategory.CONFIDENCE,
                title="Decision confidence",
                description=(
                    f"Confidence is {confidence.level.value} "
                    f"with a score of {confidence.score:.1f} out of 100."
                ),
                sequence=sequence,
                source="confidence_engine",
                importance=1.0,
                provenance=self._provenance("confidence"),
                metadata={
                    "score": confidence.score,
                    "level": confidence.level.value,
                },
            )
        )
        sequence += 1

        for index, reason in enumerate(
            confidence.reasons,
            start=1,
        ):
            if not reason.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"confidence.reason.{index}",
                    category=ExplanationCategory.CONFIDENCE,
                    title=f"Confidence reason {index}",
                    description=reason,
                    sequence=sequence,
                    source="confidence_engine",
                    importance=0.75,
                    provenance=self._provenance(
                        f"confidence.reasons[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        for index, missing_information in enumerate(
            confidence.missing_information,
            start=1,
        ):
            if not missing_information.strip():
                continue

            items.append(
                ExplanationItem(
                    identifier=f"confidence.missing_information.{index}",
                    category=ExplanationCategory.LIMITATION,
                    title=f"Missing information {index}",
                    description=missing_information,
                    sequence=sequence,
                    source="confidence_engine",
                    importance=0.8,
                    provenance=self._provenance(
                        f"confidence.missing_information[{index - 1}]"
                    ),
                )
            )
            sequence += 1

        return items, sequence

    def _build_evidence_items(
        self,
        evidence: list[Evidence],
        start_sequence: int,
    ) -> tuple[list[ExplanationItem], int]:
        items: list[ExplanationItem] = []
        sequence = start_sequence

        for index, evidence_item in enumerate(
            evidence,
            start=1,
        ):
            description = self._evidence_description(evidence_item)

            items.append(
                ExplanationItem(
                    identifier=f"evidence.{index}.{evidence_item.key}",
                    category=ExplanationCategory.EVIDENCE,
                    title=evidence_item.key,
                    description=description,
                    sequence=sequence,
                    source=evidence_item.source,
                    importance=evidence_item.weight,
                    provenance=self._provenance(f"evidence[{index - 1}]"),
                    metadata={
                        "evidence_type": evidence_item.evidence_type.value,
                        "value": evidence_item.value,
                    },
                )
            )
            sequence += 1

        return items, sequence

    def _build_recommendation_items(
        self,
        recommendations: list[Recommendation],
        start_sequence: int,
    ) -> tuple[list[ExplanationItem], int]:
        items: list[ExplanationItem] = []
        sequence = start_sequence

        for index, recommendation in enumerate(recommendations):
            items.append(
                ExplanationItem(
                    identifier=f"recommendation.{recommendation.order}",
                    category=ExplanationCategory.RECOMMENDATION,
                    title=recommendation.title,
                    description=recommendation.description,
                    sequence=sequence,
                    source="recommendation_engine",
                    importance=self._recommendation_importance(
                        recommendation
                    ),
                    provenance=self._provenance(
                        f"recommendations[{index}]"
                    ),
                    metadata={
                        "order": recommendation.order,
                        "action": recommendation.action.value,
                        "priority": recommendation.priority.value,
                        "owner": recommendation.owner,
                        "target_time_hours": (
                            recommendation.target_time_hours
                        ),
                        "verification_steps": list(
                            recommendation.verification_steps
                        ),
                        "dependencies": list(
                            recommendation.dependencies
                        ),
                    },
                )
            )
            sequence += 1

        return items, sequence

    @staticmethod
    def _provenance(source_reference: str) -> ExplanationProvenance:
        return ExplanationProvenance(
            source_type="decision_result",
            source_reference=source_reference,
        )

    @staticmethod
    def _evidence_description(evidence: Evidence) -> str:
        if evidence.description and evidence.description.strip():
            return evidence.description

        value = DecisionExplainabilityProjectionBuilder._stringify_value(
            evidence.value
        )

        return f"{evidence.key}: {value}"

    @staticmethod
    def _stringify_value(value: Any) -> str:
        if value is None:
            return "not available"

        if isinstance(value, bool):
            return "true" if value else "false"

        if isinstance(value, (list, tuple, set)):
            return ", ".join(str(item) for item in value)

        if isinstance(value, dict):
            return ", ".join(
                f"{key}={item}"
                for key, item in value.items()
            )

        return str(value)

    @staticmethod
    def _recommendation_importance(
        recommendation: Recommendation,
    ) -> float:
        priority_importance = {
            "critical": 1.0,
            "high": 0.9,
            "medium": 0.75,
            "low": 0.6,
            "informational": 0.4,
        }

        return priority_importance[recommendation.priority.value]


DecisionTraceBuilder = DecisionExplainabilityProjectionBuilder
