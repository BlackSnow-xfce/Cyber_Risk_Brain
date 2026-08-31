import pytest

from core.enterprise_context import BusinessImportance, ServiceImpactProfile
from core.enterprise_context.asset_business_context import ServiceCriticality
from core.enterprise_context.asset_context import AssetCriticality


def test_service_impact_profile_is_immutable_and_strict():
    profile = ServiceImpactProfile("asset-1", "Payments", BusinessImportance.HIGH,
                                   BusinessImportance.CRITICAL, BusinessImportance.LOW, "cmdb:1")
    assert profile.integrity_importance is BusinessImportance.CRITICAL
    with pytest.raises(Exception):
        profile.business_service = "Other"


@pytest.mark.parametrize("field,value", [
    ("canonical_asset_id", ""), ("canonical_asset_id", " asset-1 "),
    ("business_service", " "), ("source_reference", ""),
    ("confidentiality_importance", "HIGH"),
    ("integrity_importance", AssetCriticality.CRITICAL),
    ("availability_importance", ServiceCriticality.HIGH),
])
def test_service_impact_profile_rejects_invalid_authority(field, value):
    data = dict(canonical_asset_id="asset-1", business_service="Payments",
                confidentiality_importance=BusinessImportance.HIGH,
                integrity_importance=BusinessImportance.CRITICAL,
                availability_importance=BusinessImportance.LOW, source_reference="cmdb:1")
    data[field] = value
    with pytest.raises(ValueError):
        ServiceImpactProfile(**data)
