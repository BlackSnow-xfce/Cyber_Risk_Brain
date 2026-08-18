from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Generic, Protocol, TypeVar

from analysis.risk_engine import RiskEngine
from core.enterprise_context import AssetContext, AssetCriticality
from core.decision.models import Evidence, EvidenceKind, EvidenceType
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.models import UniversalFinding
from core.security_observation import CORRELATION_EVIDENCE_CONTRACT_VERSION
from core.threat_intelligence import (
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
)


class RiskInputState(str, Enum):
    """Availability of one authoritative risk input."""

    AUTHORITATIVE = "AUTHORITATIVE"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"


class RiskAssessmentStatus(str, Enum):
    """Outcome of the controlled technical risk assessment attempt."""

    ASSESSED = "ASSESSED"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"


class RiskAssessmentReadinessStatus(str, Enum):
    """Whether canonical evidence may enter a future risk assessment."""

    READY = "READY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


RiskValue = TypeVar("RiskValue")


@dataclass(frozen=True)
class RiskInputValue(Generic[RiskValue]):
    state: RiskInputState
    value: RiskValue | None = None
    source: str | None = None

    def __post_init__(self) -> None:
        if self.state is RiskInputState.AUTHORITATIVE:
            if self.source is None or not self.source.strip():
                raise ValueError(
                    "An authoritative risk input requires a source."
                )
            return

        if self.value is not None or self.source is not None:
            raise ValueError(
                "Unknown or unevaluated risk inputs cannot contain a value."
            )

    @classmethod
    def authoritative(
        cls,
        value: RiskValue | None,
        source: str,
    ) -> RiskInputValue[RiskValue]:
        return cls(
            state=RiskInputState.AUTHORITATIVE,
            value=value,
            source=source,
        )

    @classmethod
    def unknown(cls) -> RiskInputValue[RiskValue]:
        return cls(state=RiskInputState.UNKNOWN)

    @classmethod
    def not_evaluated(cls) -> RiskInputValue[RiskValue]:
        return cls(state=RiskInputState.NOT_EVALUATED)


@dataclass(frozen=True)
class RiskAssessmentInput:
    finding_id: str
    finding_source: str
    title: str
    vendor_severity: str
    asset: str
    business_criticality: RiskInputValue[AssetCriticality]
    exposure: RiskInputValue[bool]
    detection_available: RiskInputValue[bool]
    threat_intelligence_match: RiskInputValue[bool]
    mitre_tactic: RiskInputValue[str]

    def __post_init__(self) -> None:
        required_values = (
            ("business_criticality", self.business_criticality),
            ("exposure", self.exposure),
            ("detection_available", self.detection_available),
            (
                "threat_intelligence_match",
                self.threat_intelligence_match,
            ),
        )

        for name, risk_input in required_values:
            if (
                risk_input.state is RiskInputState.AUTHORITATIVE
                and risk_input.value is None
            ):
                raise ValueError(
                    f"Authoritative {name} requires a value."
                )

    @classmethod
    def from_universal_finding(
        cls,
        finding: UniversalFinding,
    ) -> RiskAssessmentInput:
        """Project only authoritative observation data from a finding."""

        return cls(
            finding_id=finding.id,
            finding_source=finding.source,
            title=finding.title,
            vendor_severity=finding.vendor_severity,
            asset=finding.asset,
            business_criticality=RiskInputValue.unknown(),
            exposure=RiskInputValue.not_evaluated(),
            detection_available=RiskInputValue.not_evaluated(),
            threat_intelligence_match=RiskInputValue.not_evaluated(),
            mitre_tactic=RiskInputValue.not_evaluated(),
        )

    def with_asset_context(
        self,
        asset_context: AssetContext | None,
    ) -> RiskAssessmentInput:
        if asset_context is None:
            return self

        if asset_context.observed_identifier.value != self.asset:
            raise ValueError(
                "Asset context does not match the finding asset identifier."
            )

        return replace(
            self,
            business_criticality=RiskInputValue.authoritative(
                asset_context.criticality,
                asset_context.source_reference,
            ),
        )


@dataclass(frozen=True)
class AvailableRiskInput:
    name: str
    value: str | bool | None
    source: str


@dataclass(frozen=True)
class MissingRiskInput:
    name: str
    state: RiskInputState


@dataclass(frozen=True)
class RiskAssessmentResult:
    finding_id: str
    status: RiskAssessmentStatus
    available_inputs: tuple[AvailableRiskInput, ...]
    missing_inputs: tuple[MissingRiskInput, ...]
    score: int | None


@dataclass(frozen=True, slots=True)
class RiskAssessmentReadinessResult:
    finding_id: str
    status: RiskAssessmentReadinessStatus
    reason: str
    considered_evidence_ids: tuple[str, ...]
    referenced_input_references: tuple[str, ...]
    missing_requirements: tuple[str, ...]
    completeness: ExplanationCompleteness


class RiskAssessmentReadinessInput(Protocol):
    finding_id: str
    evidence: tuple[Evidence, ...]
    completeness: ExplanationCompleteness
    asset_context: AssetContext | None
    threat_intelligence: tuple[FindingThreatIntelligence, ...]


class RiskAssessmentReadinessService:
    """Validate existing evidence without calculating or classifying risk."""

    def evaluate(
        self,
        correlation: RiskAssessmentReadinessInput,
    ) -> RiskAssessmentReadinessResult:
        evidence_ids = tuple(
            evidence.identifier
            for evidence in correlation.evidence
            if evidence.identifier is not None
        )
        input_references = tuple(
            dict.fromkeys(
                reference
                for evidence in correlation.evidence
                if evidence.provenance is not None
                for reference in evidence.provenance.input_references
            )
        )
        missing: list[str] = []

        if correlation.completeness.status is not CompletenessStatus.AVAILABLE:
            missing.append(
                "correlation_completeness:"
                f"{correlation.completeness.status.value}"
            )
        if correlation.asset_context is None:
            missing.append("canonical_asset_context")
        if not correlation.threat_intelligence:
            missing.append("threat_intelligence")
        if not correlation.evidence:
            missing.append("correlation_derived_evidence")

        evidence_by_identifier = {
            evidence.identifier: evidence
            for evidence in correlation.evidence
            if evidence.identifier is not None
        }
        if len(evidence_by_identifier) != len(correlation.evidence):
            missing.append("unique_correlation_evidence_identifier")

        for relationship in correlation.threat_intelligence:
            vulnerability = relationship.vulnerability
            if (
                relationship.applicability
                is not FindingIntelligenceApplicability.APPLICABLE
                or vulnerability is None
            ):
                missing.append("applicable_threat_intelligence")
                continue
            for name, fact in (
                ("nvd", vulnerability.nvd),
                ("cvss", vulnerability.cvss),
                ("epss", vulnerability.epss),
                ("cisa_kev", vulnerability.cisa_kev),
            ):
                if fact.completeness.status is not CompletenessStatus.AVAILABLE:
                    missing.append(
                        f"threat_intelligence.{name}:"
                        f"{fact.completeness.status.value}"
                    )
            cve = vulnerability.cve_identifier.value
            expected_evidence_id = (
                f"correlation:{correlation.finding_id}:{cve}"
            )
            matching_evidence = evidence_by_identifier.get(
                expected_evidence_id
            )
            if matching_evidence is None:
                missing.append(
                    f"correlation_derived_evidence:{cve}"
                )
                continue
            references = (
                matching_evidence.provenance.input_references
                if matching_evidence.provenance is not None
                else ()
            )
            for name, fact in (
                ("nvd", vulnerability.nvd),
                ("cvss", vulnerability.cvss),
                ("epss", vulnerability.epss),
                ("cisa-kev", vulnerability.cisa_kev),
            ):
                expected_reference = (
                    f"threat-intelligence:{cve}:{name}:"
                    f"{fact.provenance.source_reference}"
                )
                if expected_reference not in references:
                    missing.append(
                        f"threat_intelligence_evidence_reference:"
                        f"{cve}:{name}"
                    )

        for evidence in correlation.evidence:
            self._validate_evidence(correlation, evidence, missing)

        missing_requirements = tuple(dict.fromkeys(missing))
        if missing_requirements:
            status = RiskAssessmentReadinessStatus.INSUFFICIENT_EVIDENCE
            reason = (
                "Risk assessment evidence is insufficient: "
                + ", ".join(missing_requirements)
                + "."
            )
            completeness_status = (
                correlation.completeness.status
                if correlation.completeness.status
                is not CompletenessStatus.AVAILABLE
                else CompletenessStatus.NO_DATA
            )
            source_reference = "risk-assessment-readiness:insufficient"
        else:
            status = RiskAssessmentReadinessStatus.READY
            reason = (
                "Canonical asset context, required threat intelligence, "
                "and correlation derived evidence are available and consistent."
            )
            completeness_status = CompletenessStatus.AVAILABLE
            source_reference = "risk-assessment-readiness:ready"

        return RiskAssessmentReadinessResult(
            finding_id=correlation.finding_id,
            status=status,
            reason=reason,
            considered_evidence_ids=evidence_ids,
            referenced_input_references=input_references,
            missing_requirements=missing_requirements,
            completeness=ExplanationCompleteness(
                status=completeness_status,
                provenance=ExplanationProvenance(
                    source_type="risk_assessment_readiness",
                    source_reference=(
                        f"{source_reference}:{correlation.finding_id}"
                    ),
                ),
            ),
        )

    @staticmethod
    def _validate_evidence(
        correlation: RiskAssessmentReadinessInput,
        evidence: Evidence,
        missing: list[str],
    ) -> None:
        if not hasattr(evidence, "kind"):
            missing.append("canonical_evidence_metadata")
            return
        if evidence.kind is not EvidenceKind.DERIVED:
            missing.append("correlation_evidence_kind:derived")
        if evidence.evidence_type is not EvidenceType.CORRELATION:
            missing.append("correlation_evidence_type:correlation")
        if evidence.contract_version != CORRELATION_EVIDENCE_CONTRACT_VERSION:
            missing.append("correlation_evidence_contract:1.0")
        if evidence.identifier is None or not evidence.identifier.strip():
            missing.append("correlation_evidence_identifier")
        if evidence.provenance is None:
            missing.append("correlation_evidence_provenance")
            return
        references = evidence.provenance.input_references
        if not any(
            reference.startswith(f"finding:")
            and reference.endswith(f":{correlation.finding_id}")
            for reference in references
        ):
            missing.append("finding_evidence_reference")
        asset_context = correlation.asset_context
        if asset_context is not None:
            expected_asset_reference = (
                f"asset-context:{asset_context.canonical_asset_id}:"
                f"{asset_context.source_reference}"
            )
            if expected_asset_reference not in references:
                missing.append("asset_context_evidence_reference")


class RiskScoreCalculator(Protocol):
    def calculate_risk_score(
        self,
        node: dict[str, object],
    ) -> int: ...


class RiskReadinessService:
    """Gate the existing risk calculation behind explicit completeness."""

    def __init__(
        self,
        risk_engine: RiskScoreCalculator | None = None,
    ) -> None:
        self._risk_engine = risk_engine or RiskEngine()

    def assess_finding(
        self,
        finding: UniversalFinding,
    ) -> RiskAssessmentResult:
        return self.assess(
            RiskAssessmentInput.from_universal_finding(finding)
        )

    def assess(
        self,
        assessment_input: RiskAssessmentInput,
    ) -> RiskAssessmentResult:
        risk_values = self._risk_values(assessment_input)
        missing_inputs = tuple(
            MissingRiskInput(name=name, state=value.state)
            for name, value in risk_values
            if value.state is not RiskInputState.AUTHORITATIVE
        )

        available_inputs = self._available_inputs(
            assessment_input,
            risk_values,
        )

        if missing_inputs:
            return RiskAssessmentResult(
                finding_id=assessment_input.finding_id,
                status=RiskAssessmentStatus.INSUFFICIENT_CONTEXT,
                available_inputs=available_inputs,
                missing_inputs=missing_inputs,
                score=None,
            )

        score = self._risk_engine.calculate_risk_score(
            self._risk_node(assessment_input)
        )

        return RiskAssessmentResult(
            finding_id=assessment_input.finding_id,
            status=RiskAssessmentStatus.ASSESSED,
            available_inputs=available_inputs,
            missing_inputs=(),
            score=score,
        )

    @staticmethod
    def _risk_values(
        assessment_input: RiskAssessmentInput,
    ) -> tuple[tuple[str, RiskInputValue[object]], ...]:
        return (
            (
                "business_criticality",
                assessment_input.business_criticality,
            ),
            ("exposure", assessment_input.exposure),
            (
                "detection_available",
                assessment_input.detection_available,
            ),
            (
                "threat_intelligence_match",
                assessment_input.threat_intelligence_match,
            ),
            ("mitre_tactic", assessment_input.mitre_tactic),
        )

    @staticmethod
    def _available_inputs(
        assessment_input: RiskAssessmentInput,
        risk_values: tuple[tuple[str, RiskInputValue[object]], ...],
    ) -> tuple[AvailableRiskInput, ...]:
        observation_inputs = (
            AvailableRiskInput(
                name="finding_source",
                value=assessment_input.finding_source,
                source=assessment_input.finding_source,
            ),
            AvailableRiskInput(
                name="title",
                value=assessment_input.title,
                source=assessment_input.finding_source,
            ),
            AvailableRiskInput(
                name="vendor_severity",
                value=assessment_input.vendor_severity,
                source=assessment_input.finding_source,
            ),
            AvailableRiskInput(
                name="asset",
                value=assessment_input.asset,
                source=assessment_input.finding_source,
            ),
        )
        authoritative_risk_inputs = tuple(
            AvailableRiskInput(
                name=name,
                value=(
                    value.value.value
                    if isinstance(value.value, Enum)
                    else value.value
                ),
                source=value.source or "",
            )
            for name, value in risk_values
            if value.state is RiskInputState.AUTHORITATIVE
        )
        return observation_inputs + authoritative_risk_inputs

    @staticmethod
    def _risk_node(
        assessment_input: RiskAssessmentInput,
    ) -> dict[str, object]:
        criticality = assessment_input.business_criticality.value

        if criticality is None:
            raise ValueError(
                "Authoritative business criticality requires a value."
            )

        return {
            "criticality": criticality.value,
            "exposed": assessment_input.exposure.value,
            "detection": assessment_input.detection_available.value,
            "threat_intel": (
                assessment_input.threat_intelligence_match.value
            ),
            "mitre": assessment_input.mitre_tactic.value,
        }
