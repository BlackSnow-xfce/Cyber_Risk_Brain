from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.finding_asset_business_context import (
    FindingAssetBusinessContextResolution,
    FindingAssetBusinessContextResolutionStatus,
)


class BusinessImpactReadinessStatus(str, Enum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class BusinessContextFact:
    name: str
    value: str
    source_reference: str


@dataclass(frozen=True, slots=True)
class BusinessImpactReadiness:
    status: BusinessImpactReadinessStatus
    reason: str
    facts: tuple[BusinessContextFact, ...]
    missing_requirements: tuple[str, ...]
    source_references: tuple[str, ...]


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
                status=BusinessImpactReadinessStatus.UNAVAILABLE,
                reason="Business impact readiness is unavailable because authoritative business context is missing.",
                facts=(),
                missing_requirements=missing,
                source_references=(),
            )
        facts = (
            BusinessContextFact("canonical_asset_id", context.canonical_asset_id, context.source_reference),
            BusinessContextFact("business_service", context.business_service, context.source_reference),
            BusinessContextFact("environment", context.environment.value, context.source_reference),
            BusinessContextFact("service_criticality", context.service_criticality.value, context.source_reference),
        )
        return BusinessImpactReadiness(
            status=BusinessImpactReadinessStatus.READY,
            reason="All approved authoritative business-context facts are available.",
            facts=facts,
            missing_requirements=(),
            source_references=(context.source_reference,),
        )
