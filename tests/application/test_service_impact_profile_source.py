import json

import pytest

from application.service_impact_profile import ServiceImpactProfileDataError, ServiceImpactProfileQueryService
from core.enterprise_context import BusinessImportance


def _record(**changes):
    value = {"canonicalAssetId": "asset-1", "businessService": "Payments",
             "confidentialityImportance": "HIGH", "integrityImportance": "CRITICAL",
             "availabilityImportance": "LOW", "sourceReference": "cmdb:1"}
    value.update(changes)
    return value


def _write(tmp_path, records, root="serviceImpactProfiles"):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps({root: records}), encoding="utf-8")
    return str(path)


def test_strict_source_resolves_exact_profile(tmp_path):
    result = ServiceImpactProfileQueryService(_write(tmp_path, [_record()])).resolve("asset-1")
    assert result and result.confidentiality_importance is BusinessImportance.HIGH


@pytest.mark.parametrize("records", [
    [_record(), _record()], [_record(environment="x")],
    [_record(confidentialityImportance="high")], [_record(sourceReference="")],
])
def test_source_rejects_duplicates_unknown_keys_and_invalid_values(tmp_path, records):
    with pytest.raises(ServiceImpactProfileDataError):
        ServiceImpactProfileQueryService(_write(tmp_path, records)).resolve("asset-1")


def test_unconfigured_and_missing_records_are_truthfully_absent(tmp_path):
    assert ServiceImpactProfileQueryService(None).resolve("asset-1") is None
    assert ServiceImpactProfileQueryService(_write(tmp_path, [])).resolve("asset-1") is None
