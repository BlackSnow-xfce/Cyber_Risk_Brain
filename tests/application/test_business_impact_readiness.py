from dataclasses import replace

import pytest

from application.business_impact_readiness import (
    BusinessContextFact, BusinessImpactReadiness,
    BusinessImpactReadinessService, BusinessImpactReadinessStatus,
)
from application.finding_asset_business_context import FindingAssetBusinessContextResolution, FindingAssetBusinessContextResolutionStatus
from core.enterprise_context import AssetBusinessContext, BusinessEnvironment, ServiceCriticality
from core.explainability import CompletenessStatus, ExplanationCompleteness, ExplanationProvenance


def _completeness(status, outcome="ready", finding_id="finding-1"):
    return ExplanationCompleteness(
        status=status,
        provenance=ExplanationProvenance(
            "business_impact_readiness",
            f"business-impact-readiness:{outcome}:{finding_id}",
        ),
    )


def _valid_ready(**changes):
    values = dict(
        finding_id="finding-1", status=BusinessImpactReadinessStatus.READY,
        reason="Complete authority.",
        facts=(
            BusinessContextFact("canonical_asset_id", "asset-1", "cmdb:1"),
            BusinessContextFact("business_service", "Payments", "cmdb:1"),
            BusinessContextFact("environment", "PRODUCTION", "cmdb:1"),
            BusinessContextFact("service_criticality", "CRITICAL", "cmdb:1"),
        ),
        missing_requirements=(), source_references=("cmdb:1",),
        completeness=_completeness(CompletenessStatus.AVAILABLE),
    )
    values.update(changes)
    return BusinessImpactReadiness(**values)


def test_complete_authoritative_context_is_ready_with_per_fact_provenance():
    context = AssetBusinessContext("asset-1", "Payments", BusinessEnvironment.PRODUCTION,
                                   ServiceCriticality.CRITICAL, "cmdb:1")
    result = BusinessImpactReadinessService().evaluate(FindingAssetBusinessContextResolution(
        "finding-1", FindingAssetBusinessContextResolutionStatus.RESOLVED, context))
    assert result.status is BusinessImpactReadinessStatus.READY
    assert result.missing_requirements == ()
    assert all(fact.source_reference == "cmdb:1" for fact in result.facts)
    assert result.finding_id == "finding-1"
    assert result.completeness.status is CompletenessStatus.AVAILABLE


def test_absent_context_is_unavailable_with_exact_missing_requirements():
    result = BusinessImpactReadinessService().evaluate(FindingAssetBusinessContextResolution(
        "finding-1", FindingAssetBusinessContextResolutionStatus.NOT_FOUND))
    assert result.status is BusinessImpactReadinessStatus.UNAVAILABLE
    assert result.missing_requirements == ("business_service", "environment", "service_criticality", "business_context_provenance")
    assert result.completeness.status is CompletenessStatus.NO_DATA


@pytest.mark.parametrize("field,value", [
    ("name", ""), ("name", "  "), ("name", 1),
    ("value", ""), ("value", "  "), ("value", 1),
    ("source_reference", ""), ("source_reference", "  "),
    ("source_reference", 1),
])
def test_business_context_fact_rejects_invalid_runtime_values(field, value):
    data = {"name": "environment", "value": "PRODUCTION", "source_reference": "cmdb:1"}
    data[field] = value
    with pytest.raises(ValueError):
        BusinessContextFact(**data)


@pytest.mark.parametrize("changes", [
    {"finding_id": ""},
    {"missing_requirements": ("business_service",)},
    {"facts": ()},
    {"facts": (
        BusinessContextFact("canonical_asset_id", "asset-1", "cmdb:1"),
        BusinessContextFact("business_service", "Payments", "cmdb:1"),
        BusinessContextFact("environment", "PRODUCTION", "cmdb:1"),
    )},
    {"source_references": ()},
    {"completeness": _completeness(CompletenessStatus.NO_DATA)},
    {"completeness": ExplanationCompleteness(
        CompletenessStatus.AVAILABLE,
        ExplanationProvenance("other", "other:ready:finding-1"),
    )},
])
def test_ready_rejects_incomplete_or_unproven_states(changes):
    with pytest.raises(ValueError):
        _valid_ready(**changes)


def test_valid_ready_construction_succeeds():
    assert _valid_ready().status is BusinessImpactReadinessStatus.READY


def test_unavailable_preserves_requirements_and_rejects_available_completeness():
    result = BusinessImpactReadiness(
        finding_id="finding-1", status=BusinessImpactReadinessStatus.UNAVAILABLE,
        reason="Missing service.", facts=(),
        missing_requirements=("business_service",), source_references=(),
        completeness=_completeness(CompletenessStatus.NO_DATA, "unavailable"),
    )
    assert result.missing_requirements == ("business_service",)
    with pytest.raises(ValueError):
        replace(result, completeness=_completeness(CompletenessStatus.AVAILABLE, "unavailable"))
