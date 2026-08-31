from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.finding_asset_business_context import FindingAssetBusinessContextResolution, FindingAssetBusinessContextResolutionStatus
from application.service_impact_profile import ServiceImpactProfileQueryService
from core.enterprise_context import ServiceImpactProfile


class FindingServiceImpactProfileIntegrityError(ValueError):
    pass


class FindingServiceImpactProfileResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    MISSING_CANONICAL_ASSET = "MISSING_CANONICAL_ASSET"


@dataclass(frozen=True, slots=True)
class FindingServiceImpactProfileResolution:
    finding_id: str
    status: FindingServiceImpactProfileResolutionStatus
    profile: ServiceImpactProfile | None = None

    def __post_init__(self) -> None:
        if type(self.finding_id) is not str or not self.finding_id.strip():
            raise ValueError("Service impact profile resolution requires a finding ID.")
        if (self.status is FindingServiceImpactProfileResolutionStatus.RESOLVED) != (self.profile is not None):
            raise ValueError("Service impact profile resolution state is inconsistent.")


class FindingServiceImpactProfileUseCase:
    def __init__(self, profiles: ServiceImpactProfileQueryService) -> None:
        self._profiles = profiles

    def resolve(self, business_context: FindingAssetBusinessContextResolution) -> FindingServiceImpactProfileResolution:
        context = business_context.context
        if business_context.status is FindingAssetBusinessContextResolutionStatus.MISSING_CANONICAL_ASSET:
            return FindingServiceImpactProfileResolution(business_context.finding_id, FindingServiceImpactProfileResolutionStatus.MISSING_CANONICAL_ASSET)
        if context is None:
            return FindingServiceImpactProfileResolution(business_context.finding_id, FindingServiceImpactProfileResolutionStatus.NOT_FOUND)
        profile = self._profiles.resolve(context.canonical_asset_id)
        if profile is None:
            return FindingServiceImpactProfileResolution(business_context.finding_id, FindingServiceImpactProfileResolutionStatus.NOT_FOUND)
        if profile.canonical_asset_id != context.canonical_asset_id or profile.business_service != context.business_service:
            raise FindingServiceImpactProfileIntegrityError("Service impact profile does not match the authoritative business-context snapshot.")
        return FindingServiceImpactProfileResolution(business_context.finding_id, FindingServiceImpactProfileResolutionStatus.RESOLVED, profile)
