from application.business_impact_classification_readiness import BusinessImpactClassificationReadinessService, BusinessImpactClassificationReadinessStatus
from application.business_impact_readiness import BusinessContextFact, BusinessImpactReadiness, BusinessImpactReadinessStatus
from application.finding_service_impact_profile import FindingServiceImpactProfileResolution, FindingServiceImpactProfileResolutionStatus
from application.finding_technical_effect import FindingTechnicalEffect, FindingTechnicalEffectProjection, FindingTechnicalEffectStatus, TechnicalEffectLevel
from core.enterprise_context import BusinessImportance, ServiceImpactProfile
from core.explainability import CompletenessStatus, ExplanationCompleteness, ExplanationProvenance


def _complete(status, source, reference):
    return ExplanationCompleteness(status, ExplanationProvenance(source, reference))


def _business():
    facts = tuple(BusinessContextFact(n, v, "cmdb:1") for n, v in (("canonical_asset_id", "asset-1"), ("business_service", "Payments"), ("environment", "PRODUCTION"), ("service_criticality", "HIGH")))
    return BusinessImpactReadiness("finding-1", BusinessImpactReadinessStatus.READY, "Ready", facts, (), ("cmdb:1",), _complete(CompletenessStatus.AVAILABLE, "business_impact_readiness", "business-impact-readiness:ready:finding-1"))


def _profile(profile=True):
    value = ServiceImpactProfile("asset-1", "Payments", BusinessImportance.HIGH, BusinessImportance.CRITICAL, BusinessImportance.LOW, "bia:1") if profile else None
    return FindingServiceImpactProfileResolution("finding-1", FindingServiceImpactProfileResolutionStatus.RESOLVED if profile else FindingServiceImpactProfileResolutionStatus.NOT_FOUND, value)


def _technical(available=True):
    effects = (FindingTechnicalEffect("finding-1", "CVE-2024-1234", "CVSS:3.1/C:H/I:L/A:N", TechnicalEffectLevel.HIGH, TechnicalEffectLevel.LOW, TechnicalEffectLevel.NONE, "nvd:1", None),) if available else ()
    status = FindingTechnicalEffectStatus.AVAILABLE if available else FindingTechnicalEffectStatus.UNAVAILABLE
    return FindingTechnicalEffectProjection("finding-1", status, effects, () if available else ("technical_effect",), _complete(CompletenessStatus.AVAILABLE if available else CompletenessStatus.NO_DATA, "finding_technical_effect", f"finding-technical-effect:{status.value.lower()}:finding-1"))


def test_complete_authority_is_ready_without_business_impact():
    result = BusinessImpactClassificationReadinessService().evaluate(_business(), _profile(), _technical())
    assert result.status is BusinessImpactClassificationReadinessStatus.READY
    assert result.missing_requirements == ()


def test_missing_profile_or_technical_effect_is_unavailable():
    for profile, technical in ((_profile(False), _technical()), (_profile(), _technical(False))):
        result = BusinessImpactClassificationReadinessService().evaluate(_business(), profile, technical)
        assert result.status is BusinessImpactClassificationReadinessStatus.UNAVAILABLE
        assert result.missing_requirements
