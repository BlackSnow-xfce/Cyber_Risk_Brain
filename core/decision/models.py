from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class DecisionPriority(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class DecisionAction(StrEnum):
    REMEDIATE_NOW = "remediate_now"
    REMEDIATE_PLANNED = "remediate_planned"
    MITIGATE = "mitigate"
    INVESTIGATE = "investigate"
    MONITOR = "monitor"
    ACCEPT = "accept"


class ConfidenceLevel(StrEnum):
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class EvidenceType(StrEnum):
    FINDING = "finding"
    ASSET = "asset"
    THREAT_INTELLIGENCE = "threat_intelligence"
    EXPOSURE = "exposure"
    BUSINESS_CONTEXT = "business_context"
    CORRELATION = "correlation"
    RISK_SCORE = "risk_score"
    ATTACK_PATH = "attack_path"
    CONTROL = "control"
    WEB_TELEMETRY = "web_telemetry"
    OTHER = "other"


class EvidenceKind(StrEnum):
    SOURCE = "source"
    DERIVED = "derived"


@dataclass(frozen=True, slots=True)
class EvidenceProvenance:
    source_type: str
    source_reference: str
    input_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.source_type.strip():
            raise ValueError("Evidence provenance source type must not be empty.")
        if not self.source_reference.strip():
            raise ValueError(
                "Evidence provenance source reference must not be empty."
            )
        if any(not reference.strip() for reference in self.input_references):
            raise ValueError("Evidence input references must not be empty.")
        if len(set(self.input_references)) != len(self.input_references):
            raise ValueError("Evidence input references must be unique.")


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_type: EvidenceType
    key: str
    value: Any
    source: str | None = None
    description: str | None = None
    weight: float = 1.0
    identifier: str | None = None
    kind: EvidenceKind | None = None
    provenance: EvidenceProvenance | None = None
    contract_version: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("Evidence key must not be empty.")

        if self.weight < 0:
            raise ValueError("Evidence weight must be greater than or equal to 0.")

        canonical_fields = (
            self.identifier,
            self.kind,
            self.provenance,
            self.contract_version,
        )
        if any(field is not None for field in canonical_fields) and any(
            field is None for field in canonical_fields
        ):
            raise ValueError(
                "Canonical evidence metadata must be supplied completely."
            )
        if self.identifier is not None and not self.identifier.strip():
            raise ValueError("Evidence identifier must not be empty.")
        if self.contract_version is not None and not self.contract_version.strip():
            raise ValueError("Evidence contract version must not be empty.")
        if self.kind is EvidenceKind.DERIVED:
            if self.provenance is None or not self.provenance.input_references:
                raise ValueError(
                    "Derived evidence must reference its input evidence."
                )


@dataclass(slots=True)
class AttackReasoning:
    summary: str
    attack_vector: str | None = None
    exploitation_probability: str | None = None
    likely_outcomes: list[str] = field(default_factory=list)
    attack_steps: list[str] = field(default_factory=list)
    supporting_factors: list[str] = field(default_factory=list)
    limiting_factors: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("Attack reasoning summary must not be empty.")


@dataclass(slots=True)
class BusinessImpact:
    summary: str
    business_service: str | None = None
    asset_criticality: str | None = None
    confidentiality_impact: str | None = None
    integrity_impact: str | None = None
    availability_impact: str | None = None
    financial_impact: str | None = None
    operational_impact: str | None = None
    regulatory_impact: str | None = None
    reputational_impact: str | None = None
    affected_processes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError("Business impact summary must not be empty.")


@dataclass(slots=True)
class Confidence:
    score: float
    level: ConfidenceLevel
    reasons: list[str] = field(default_factory=list)
    missing_information: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 100:
            raise ValueError("Confidence score must be between 0 and 100.")


@dataclass(slots=True)
class Recommendation:
    title: str
    description: str
    action: DecisionAction
    priority: DecisionPriority
    order: int
    owner: str | None = None
    target_time_hours: int | None = None
    verification_steps: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.title.strip():
            raise ValueError("Recommendation title must not be empty.")

        if not self.description.strip():
            raise ValueError("Recommendation description must not be empty.")

        if self.order < 1:
            raise ValueError("Recommendation order must be greater than 0.")

        if self.target_time_hours is not None and self.target_time_hours < 0:
            raise ValueError(
                "Recommendation target time must be greater than or equal to 0."
            )


@dataclass(slots=True)
class DecisionResult:
    finding_id: str
    priority: DecisionPriority
    action: DecisionAction
    decision: str
    attack_reasoning: AttackReasoning
    business_impact: BusinessImpact
    confidence: Confidence
    recommendations: list[Recommendation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Finding ID must not be empty.")

        if not self.decision.strip():
            raise ValueError("Decision must not be empty.")

        self.recommendations.sort(key=lambda recommendation: recommendation.order)

    @property
    def requires_immediate_action(self) -> bool:
        return self.action == DecisionAction.REMEDIATE_NOW

    @property
    def confidence_score(self) -> float:
        return self.confidence.score

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "priority": self.priority.value,
            "action": self.action.value,
            "decision": self.decision,
            "attack_reasoning": {
                "summary": self.attack_reasoning.summary,
                "attack_vector": self.attack_reasoning.attack_vector,
                "exploitation_probability": (
                    self.attack_reasoning.exploitation_probability
                ),
                "likely_outcomes": self.attack_reasoning.likely_outcomes,
                "attack_steps": self.attack_reasoning.attack_steps,
                "supporting_factors": self.attack_reasoning.supporting_factors,
                "limiting_factors": self.attack_reasoning.limiting_factors,
            },
            "business_impact": {
                "summary": self.business_impact.summary,
                "business_service": self.business_impact.business_service,
                "asset_criticality": self.business_impact.asset_criticality,
                "confidentiality_impact": (
                    self.business_impact.confidentiality_impact
                ),
                "integrity_impact": self.business_impact.integrity_impact,
                "availability_impact": self.business_impact.availability_impact,
                "financial_impact": self.business_impact.financial_impact,
                "operational_impact": self.business_impact.operational_impact,
                "regulatory_impact": self.business_impact.regulatory_impact,
                "reputational_impact": self.business_impact.reputational_impact,
                "affected_processes": self.business_impact.affected_processes,
            },
            "confidence": {
                "score": self.confidence.score,
                "level": self.confidence.level.value,
                "reasons": self.confidence.reasons,
                "missing_information": self.confidence.missing_information,
            },
            "recommendations": [
                {
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "action": recommendation.action.value,
                    "priority": recommendation.priority.value,
                    "order": recommendation.order,
                    "owner": recommendation.owner,
                    "target_time_hours": recommendation.target_time_hours,
                    "verification_steps": recommendation.verification_steps,
                    "dependencies": recommendation.dependencies,
                }
                for recommendation in self.recommendations
            ],
            "evidence": [
                {
                    "evidence_type": item.evidence_type.value,
                    "key": item.key,
                    "value": item.value,
                    "source": item.source,
                    "description": item.description,
                    "weight": item.weight,
                }
                for item in self.evidence
            ],
            "metadata": self.metadata,
        }
