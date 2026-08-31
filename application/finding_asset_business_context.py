from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.asset_business_context import AssetBusinessContextQueryService
from application.finding_asset_context import FindingAssetContextResolution
from core.enterprise_context import AssetBusinessContext


class FindingAssetBusinessContextResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    MISSING_CANONICAL_ASSET = "MISSING_CANONICAL_ASSET"


@dataclass(frozen=True, slots=True)
class FindingAssetBusinessContextResolution:
    finding_id: str
    status: FindingAssetBusinessContextResolutionStatus
    context: AssetBusinessContext | None = None

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Business context resolution requires a finding ID.")
        if (self.status is FindingAssetBusinessContextResolutionStatus.RESOLVED) != (
            self.context is not None
        ):
            raise ValueError("Business context resolution state is inconsistent.")


class FindingAssetBusinessContextUseCase:
    def __init__(self, contexts: AssetBusinessContextQueryService) -> None:
        self._contexts = contexts

    def resolve(
        self, asset_resolution: FindingAssetContextResolution
    ) -> FindingAssetBusinessContextResolution:
        asset = asset_resolution.asset_context
        if asset is None:
            return FindingAssetBusinessContextResolution(
                finding_id=asset_resolution.finding_id,
                status=FindingAssetBusinessContextResolutionStatus.MISSING_CANONICAL_ASSET,
            )
        context = self._contexts.resolve(asset.canonical_asset_id)
        return FindingAssetBusinessContextResolution(
            finding_id=asset_resolution.finding_id,
            status=(
                FindingAssetBusinessContextResolutionStatus.RESOLVED
                if context is not None
                else FindingAssetBusinessContextResolutionStatus.NOT_FOUND
            ),
            context=context,
        )
