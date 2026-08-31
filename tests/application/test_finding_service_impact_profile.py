import pytest

from application.finding_asset_business_context import FindingAssetBusinessContextResolution, FindingAssetBusinessContextResolutionStatus
from application.finding_service_impact_profile import FindingServiceImpactProfileIntegrityError, FindingServiceImpactProfileResolutionStatus, FindingServiceImpactProfileUseCase
from core.enterprise_context import AssetBusinessContext, BusinessEnvironment, BusinessImportance, ServiceCriticality, ServiceImpactProfile


class Profiles:
    def __init__(self, profile): self.profile = profile
    def resolve(self, _): return self.profile


def _business(service="Payments"):
    return FindingAssetBusinessContextResolution("finding-1", FindingAssetBusinessContextResolutionStatus.RESOLVED,
        AssetBusinessContext("asset-1", service, BusinessEnvironment.PRODUCTION, ServiceCriticality.HIGH, "cmdb:1"))


def _profile(asset="asset-1", service="Payments"):
    return ServiceImpactProfile(asset, service, BusinessImportance.HIGH, BusinessImportance.CRITICAL, BusinessImportance.LOW, "bia:1")


def test_exact_snapshot_resolves():
    assert FindingServiceImpactProfileUseCase(Profiles(_profile())).resolve(_business()).status is FindingServiceImpactProfileResolutionStatus.RESOLVED


@pytest.mark.parametrize("profile", [_profile(asset="asset-2"), _profile(service="Other")])
def test_snapshot_mismatch_fails_closed(profile):
    with pytest.raises(FindingServiceImpactProfileIntegrityError):
        FindingServiceImpactProfileUseCase(Profiles(profile)).resolve(_business())


def test_missing_profile_is_not_found():
    assert FindingServiceImpactProfileUseCase(Profiles(None)).resolve(_business()).status is FindingServiceImpactProfileResolutionStatus.NOT_FOUND
