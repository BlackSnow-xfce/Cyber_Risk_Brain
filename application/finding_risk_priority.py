from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from application.risk_readiness import (
    RiskAssessmentReadinessResult,
    RiskAssessmentReadinessStatus,
    RiskAssessmentResult,
    RiskAssessmentStatus,
)
from core.decision.models import DecisionPriority
from core.decision.priority_engine import PriorityEngine
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)


class FindingRiskPriorityStatus(str, Enum):
    PRIORITIZED = "PRIORITIZED"
    UNAVAILABLE = "UNAVAILABLE"


class RiskPriorityClassifier(Protocol):
    def calculate(self, risk_score: int) -> DecisionPriority: ...


@dataclass(frozen=True, slots=True)
class FindingRiskPriority:
    finding_id: str
    status: FindingRiskPriorityStatus
    band: DecisionPriority | None
    score: int | None
    reason: str
    considered_evidence_ids: tuple[str, ...]
    referenced_input_references: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    completeness: ExplanationCompleteness

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Finding risk priority requires a finding ID.")
        if not self.reason.strip():
            raise ValueError("Finding risk priority requires a truthful reason.")

        if self.status is FindingRiskPriorityStatus.UNAVAILABLE:
            if self.band is not None or self.score is not None:
                raise ValueError(
                    "Unavailable priority must not contain a band or score."
                )
            if self.completeness.status is CompletenessStatus.AVAILABLE:
                raise ValueError(
                    "Unavailable priority cannot claim available completeness."
                )
            return

        if self.status is not FindingRiskPriorityStatus.PRIORITIZED:
            raise ValueError("Unsupported finding risk priority status.")
        if self.band is None:
            raise ValueError("Prioritized result requires a priority band.")
        if (
            self.score is None
            or isinstance(self.score, bool)
            or not 0 <= self.score <= 100
        ):
            raise ValueError(
                "Prioritized result requires a bounded authoritative score."
            )
        if self.missing_requirements:
            raise ValueError(
                "Prioritized result cannot retain missing requirements."
            )
        if self.completeness.status is not CompletenessStatus.AVAILABLE:
            raise ValueError(
                "Prioritized result requires available completeness."
            )
        if (
            not self.considered_evidence_ids
            or not all(item.strip() for item in self.considered_evidence_ids)
            or not self.referenced_input_references
            or not all(
                item.strip() for item in self.referenced_input_references
            )
        ):
            raise ValueError(
                "Prioritized result requires evidence and input provenance."
            )


class FindingRiskPriorityService:
    """Classify only a score admitted by both authoritative readiness gates."""

    def __init__(
        self,
        classifier: RiskPriorityClassifier | None = None,
    ) -> None:
        self._classifier = classifier or PriorityEngine()

    def prioritize(
        self,
        finding_id: str,
        assessment: RiskAssessmentResult,
        evidence_readiness: RiskAssessmentReadinessResult,
    ) -> FindingRiskPriority:
        self._validate_identity(finding_id, assessment, evidence_readiness)

        missing = self._missing_requirements(assessment, evidence_readiness)
        input_references = self._input_references(
            assessment,
            evidence_readiness,
        )
        if missing:
            return FindingRiskPriority(
                finding_id=finding_id,
                status=FindingRiskPriorityStatus.UNAVAILABLE,
                band=None,
                score=None,
                reason=(
                    "Finding risk priority is unavailable because required "
                    "authoritative context or evidence is missing: "
                    + ", ".join(missing)
                    + "."
                ),
                considered_evidence_ids=(
                    evidence_readiness.considered_evidence_ids
                ),
                referenced_input_references=input_references,
                missing_requirements=missing,
                completeness=self._completeness(
                    finding_id,
                    CompletenessStatus.NO_DATA,
                    "unavailable",
                ),
            )

        score = assessment.score
        if score is None or isinstance(score, bool) or not 0 <= score <= 100:
            raise ValueError("Assessed risk must contain a bounded score.")
        if (
            not evidence_readiness.considered_evidence_ids
            or not evidence_readiness.referenced_input_references
            or evidence_readiness.completeness.status
            is not CompletenessStatus.AVAILABLE
        ):
            raise ValueError(
                "Ready risk evidence must retain identifiers and provenance."
            )

        band = self._classifier.calculate(score)
        return FindingRiskPriority(
            finding_id=finding_id,
            status=FindingRiskPriorityStatus.PRIORITIZED,
            band=band,
            score=score,
            reason=(
                "Priority was classified from the authoritative gated risk "
                f"score {score} using the existing priority policy."
            ),
            considered_evidence_ids=evidence_readiness.considered_evidence_ids,
            referenced_input_references=input_references,
            missing_requirements=(),
            completeness=self._completeness(
                finding_id,
                CompletenessStatus.AVAILABLE,
                "prioritized",
            ),
        )

    @staticmethod
    def _validate_identity(
        finding_id: str,
        assessment: RiskAssessmentResult,
        evidence_readiness: RiskAssessmentReadinessResult,
    ) -> None:
        if (
            not finding_id.strip()
            or assessment.finding_id != finding_id
            or evidence_readiness.finding_id != finding_id
        ):
            raise ValueError("Risk priority sources returned different findings.")

    @staticmethod
    def _missing_requirements(
        assessment: RiskAssessmentResult,
        evidence_readiness: RiskAssessmentReadinessResult,
    ) -> tuple[str, ...]:
        missing = [
            f"risk_input:{item.name}:{item.state.value}"
            for item in assessment.missing_inputs
        ]
        if assessment.status is not RiskAssessmentStatus.ASSESSED:
            missing.append(
                f"risk_assessment:{assessment.status.value}"
            )
        missing.extend(evidence_readiness.missing_requirements)
        if (
            evidence_readiness.status
            is not RiskAssessmentReadinessStatus.READY
        ):
            missing.append(
                f"evidence_readiness:{evidence_readiness.status.value}"
            )
        return tuple(dict.fromkeys(missing))

    @staticmethod
    def _input_references(
        assessment: RiskAssessmentResult,
        evidence_readiness: RiskAssessmentReadinessResult,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                (
                    *evidence_readiness.referenced_input_references,
                    *(
                        item.source
                        for item in assessment.available_inputs
                        if item.source.strip()
                    ),
                )
            )
        )

    @staticmethod
    def _completeness(
        finding_id: str,
        status: CompletenessStatus,
        outcome: str,
    ) -> ExplanationCompleteness:
        return ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type="finding_risk_priority",
                source_reference=(
                    f"finding-risk-priority:{outcome}:{finding_id}"
                ),
            ),
        )
