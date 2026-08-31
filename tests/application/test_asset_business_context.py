import json

import pytest

from application.asset_business_context import (
    AssetBusinessContextDataError,
    AssetBusinessContextQueryService,
)
from core.enterprise_context import (
    AssetBusinessContext,
    AssetCriticality,
    BusinessEnvironment,
    ServiceCriticality,
)


def test_asset_business_context_is_immutable_and_normalized():
    context = AssetBusinessContext(
        " asset-1 ", " Payments ", BusinessEnvironment.PRODUCTION,
        ServiceCriticality.CRITICAL, " cmdb:1 ",
    )
    assert context.canonical_asset_id == "asset-1"
    assert context.source_reference == "cmdb:1"
    with pytest.raises(AttributeError):
        context.business_service = "Other"


def test_asset_and_service_criticality_are_not_substitutable():
    with pytest.raises(ValueError):
        AssetBusinessContext("asset-1", "Payments", BusinessEnvironment.TEST,
                             AssetCriticality.HIGH, "cmdb:1")


def _write(tmp_path, records):
    path = tmp_path / "business-context.json"
    path.write_text(json.dumps({"assetBusinessContexts": records}), encoding="utf-8")
    return str(path)


def _record(**changes):
    value = {"canonicalAssetId": "asset-1", "businessService": "Payments",
             "environment": "PRODUCTION", "serviceCriticality": "CRITICAL",
             "sourceReference": "cmdb:1"}
    value.update(changes)
    return value


def test_resolves_strict_authoritative_record(tmp_path):
    result = AssetBusinessContextQueryService(_write(tmp_path, [_record()])).resolve("asset-1")
    assert result is not None and result.source_reference == "cmdb:1"


def test_unconfigured_and_missing_records_are_truthfully_unavailable(tmp_path):
    assert AssetBusinessContextQueryService(None).resolve("asset-1") is None
    assert AssetBusinessContextQueryService(_write(tmp_path, [])).resolve("asset-1") is None


@pytest.mark.parametrize("records", [
    [_record(), _record(sourceReference="cmdb:2")],
    [_record(environment="UNKNOWN")],
    [_record(serviceCriticality="SEVERE")],
    [_record(sourceReference="")],
    [{**_record(), "unexpected": "value"}],
])
def test_invalid_ambiguous_or_unproven_records_fail_closed(tmp_path, records):
    with pytest.raises(AssetBusinessContextDataError):
        AssetBusinessContextQueryService(_write(tmp_path, records)).resolve("asset-1")
