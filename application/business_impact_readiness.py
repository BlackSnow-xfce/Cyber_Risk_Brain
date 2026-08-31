from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import ClassVar

from application.finding_asset_business_context import (
    FindingAssetBusinessContextResolution,
    FindingAssetBusinessContextResolutionStatus,
)
from core.enterprise_context.asset_business_context import (
    BusinessEnvironment,
    ServiceCriticality,
)
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)


class BusinessImpactReadinessStatus(str, Enum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class BusinessContextFact:
    name: str
    value: str
    source_reference: str

    def __post_init__(self) -> None:
        for field_name in ("name", "value", "source_reference"):
            value = getattr(self, field_name)
            if type(value) is not str or not value.strip():
                raise ValueError(
                    f"Business context fact {field_name} must be a non-empty string."
                )
            object.__setattr__(self, field_name, value.strip())


@dataclass(frozen=True, slots=True)
class BusinessImpactReadiness:
    finding_id: str
    status: BusinessImpactReadinessStatus
    reason: str
    facts: tuple[BusinessContextFact, ...]
    missing_requirements: tuple[str, ...]
    source_references: tuple[str, ...]
    completeness: ExplanationCompleteness

    _REQUIRED_FACTS: ClassVar[frozenset[str]] = frozenset(
        {
            "canonical_asset_id",
            "business_service",
            "environment",
            "service_criticality",
        }
    )

    def __post_init__(self) -> None:
        if not isinstance(self.finding_id, str) or not self.finding_id.strip():
            raise ValueError("Business impact readiness requires a finding ID.")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise ValueError("Business impact readiness requires a truthful reason.")
        if not isinstance(self.status, BusinessImpactReadinessStatus):
            raise ValueError("Business impact readiness status is invalid.")
        if not isinstance(self.completeness, ExplanationCompleteness):
            raise ValueError("Business impact readiness completeness is invalid.")
        if (
            not isinstance(self.completeness.status, CompletenessStatus)
            or not isinstance(
                self.completeness.provenance, ExplanationProvenance
            )
        ):
            raise ValueError("Business impact readiness completeness is invalid.")
        if not isinstance(self.facts, tuple) or not all(
            isinstance(fact, BusinessContextFact) for fact in self.facts
        ):
            raise ValueError("Business impact readiness facts are invalid.")
        if not isinstance(self.missing_requirements, tuple):
            raise ValueError("Business impact readiness missing requirements are invalid.")
        if not isinstance(self.source_references, tuple):
            raise ValueError("Business impact readiness source references are invalid.")
        if not all(
            isinstance(item, str) and item.strip()
            for item in self.missing_requirements
        ):
            raise ValueError("Missing requirements must be non-empty strings.")
        if not all(
            isinstance(item, str) and item.strip()
            for item in self.source_references
        ):
            raise ValueError("Readiness source references must be non-empty strings.")
        expected_reference = (
            f"business-impact-readiness:{self.status.value.lower()}:"
            f"{self.finding_id.strip()}"
        )
        provenance = self.completeness.provenance
        if (
            provenance.source_type != "business_impact_readiness"
            or provenance.source_reference != expected_reference
        ):
            raise ValueError("Business impact readiness provenance is invalid.")
        fact_names = tuple(fact.name for fact in self.facts)
        if len(fact_names) != len(set(fact_names)):
            raise ValueError("Business impact readiness facts must be unique.")
        fact_sources = {fact.source_reference for fact in self.facts}
        if not fact_sources.issubset(set(self.source_references)):
            raise ValueError("Business context fact provenance is not referenced.")

        if self.status is BusinessImpactReadinessStatus.READY:
            if self.missing_requirements:
                raise ValueError("Ready business impact cannot retain missing requirements.")
            if set(fact_names) != self._REQUIRED_FACTS:
                raise ValueError("Ready business impact requires all authoritative facts.")
            if not self.source_references:
                raise ValueError("Ready business impact requires business context provenance.")
            if self.completeness.status is not CompletenessStatus.AVAILABLE:
                raise ValueError("Ready business impact requires available completeness.")
            facts_by_name = {fact.name: fact for fact in self.facts}
            self._require_enum_value(
                facts_by_name["environment"],
                BusinessEnvironment,
                "environment",
            )
            self._require_enum_value(
                facts_by_name["service_criticality"],
                ServiceCriticality,
                "service criticality",
            )
            return

        if self.status is not BusinessImpactReadinessStatus.UNAVAILABLE:
            raise ValueError("Business impact readiness status is unsupported.")
        if not self.missing_requirements:
            raise ValueError("Unavailable business impact requires missing requirements.")
        if self.completeness.status is CompletenessStatus.AVAILABLE:
            raise ValueError("Unavailable business impact cannot claim available completeness.")

    @staticmethod
    def _require_enum_value(
        fact: BusinessContextFact,
        authority: type[BusinessEnvironment] | type[ServiceCriticality],
        label: str,
    ) -> None:
        if type(fact.value) is not str:
            raise ValueError(f"Business context {label} fact is invalid.")
        try:
            authority(fact.value)
        except ValueError as error:
            raise ValueError(
                f"Business context {label} fact is invalid."
            ) from error


class BusinessImpactReadinessService:
    _REQUIREMENTS = (
        "canonical_asset_relationship",
        "business_service",
        "environment",
        "service_criticality",
        "business_context_provenance",
    )

    def evaluate(
        self, resolution: FindingAssetBusinessContextResolution
    ) -> BusinessImpactReadiness:
        context = resolution.context
        if (
            resolution.status is not FindingAssetBusinessContextResolutionStatus.RESOLVED
            or context is None
        ):
            missing = (
                self._REQUIREMENTS
                if resolution.status
                is FindingAssetBusinessContextResolutionStatus.MISSING_CANONICAL_ASSET
                else self._REQUIREMENTS[1:]
            )
            return BusinessImpactReadiness(
                finding_id=resolution.finding_id,
                status=BusinessImpactReadinessStatus.UNAVAILABLE,
                reason="Business impact readiness is unavailable because authoritative business context is missing.",
                facts=(),
                missing_requirements=missing,
                source_references=(),
                completeness=self._completeness(
                    resolution.finding_id,
                    BusinessImpactReadinessStatus.UNAVAILABLE,
                    CompletenessStatus.NO_DATA,
                ),
            )
        facts = (
            BusinessContextFact("canonical_asset_id", context.canonical_asset_id, context.source_reference),
            BusinessContextFact("business_service", context.business_service, context.source_reference),
            BusinessContextFact("environment", context.environment.value, context.source_reference),
            BusinessContextFact("service_criticality", context.service_criticality.value, context.source_reference),
        )
        return BusinessImpactReadiness(
            finding_id=resolution.finding_id,
            status=BusinessImpactReadinessStatus.READY,
            reason="All approved authoritative business-context facts are available.",
            facts=facts,
            missing_requirements=(),
            source_references=(context.source_reference,),
            completeness=self._completeness(
                resolution.finding_id,
                BusinessImpactReadinessStatus.READY,
                CompletenessStatus.AVAILABLE,
            ),
        )

    @staticmethod
    def _completeness(
        finding_id: str,
        status: BusinessImpactReadinessStatus,
        completeness_status: CompletenessStatus,
    ) -> ExplanationCompleteness:
        return ExplanationCompleteness(
            status=completeness_status,
            provenance=ExplanationProvenance(
                source_type="business_impact_readiness",
                source_reference=(
                    f"business-impact-readiness:{status.value.lower()}:{finding_id}"
                ),
            ),
        )
