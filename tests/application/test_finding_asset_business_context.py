from application.asset_business_context import AssetBusinessContextQueryService
from application.finding_asset_business_context import (
    FindingAssetBusinessContextResolutionStatus as Status,
    FindingAssetBusinessContextUseCase,
)
from application.finding_asset_context import FindingAssetContextResolution, FindingAssetContextResolutionStatus
from core.enterprise_context import AssetContext, AssetCriticality, AssetIdentifierType, ObservedAssetIdentifier


def _resolution(with_asset=True):
    observed = ObservedAssetIdentifier(AssetIdentifierType.IP_ADDRESS, "192.0.2.1")
    return FindingAssetContextResolution(
        "finding-1", "source", "title",
        FindingAssetContextResolutionStatus.RESOLVED if with_asset else FindingAssetContextResolutionStatus.NOT_FOUND,
        observed_identifier=observed,
        asset_context=AssetContext(observed, "asset-1", AssetCriticality.HIGH, "inventory:1") if with_asset else None,
    )


def test_missing_canonical_asset_is_explicit():
    result = FindingAssetBusinessContextUseCase(AssetBusinessContextQueryService(None)).resolve(_resolution(False))
    assert result.status is Status.MISSING_CANONICAL_ASSET


def test_missing_business_record_is_not_found():
    result = FindingAssetBusinessContextUseCase(AssetBusinessContextQueryService(None)).resolve(_resolution())
    assert result.status is Status.NOT_FOUND
