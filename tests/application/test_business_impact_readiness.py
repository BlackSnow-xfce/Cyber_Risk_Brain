from application.business_impact_readiness import BusinessImpactReadinessService, BusinessImpactReadinessStatus
from application.finding_asset_business_context import FindingAssetBusinessContextResolution, FindingAssetBusinessContextResolutionStatus
from core.enterprise_context import AssetBusinessContext, BusinessEnvironment, ServiceCriticality


def test_complete_authoritative_context_is_ready_with_per_fact_provenance():
    context = AssetBusinessContext("asset-1", "Payments", BusinessEnvironment.PRODUCTION,
                                   ServiceCriticality.CRITICAL, "cmdb:1")
    result = BusinessImpactReadinessService().evaluate(FindingAssetBusinessContextResolution(
        "finding-1", FindingAssetBusinessContextResolutionStatus.RESOLVED, context))
    assert result.status is BusinessImpactReadinessStatus.READY
    assert result.missing_requirements == ()
    assert all(fact.source_reference == "cmdb:1" for fact in result.facts)


def test_absent_context_is_unavailable_with_exact_missing_requirements():
    result = BusinessImpactReadinessService().evaluate(FindingAssetBusinessContextResolution(
        "finding-1", FindingAssetBusinessContextResolutionStatus.NOT_FOUND))
    assert result.status is BusinessImpactReadinessStatus.UNAVAILABLE
    assert result.missing_requirements == ("business_service", "environment", "service_criticality", "business_context_provenance")
