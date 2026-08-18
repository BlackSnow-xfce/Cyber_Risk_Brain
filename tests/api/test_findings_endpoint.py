import pytest
from fastapi import HTTPException

import api_app
from application import FindingsConfigurationError
from core.models import UniversalFinding


class StubFindingsQueryService:
    def get_findings(self) -> list[UniversalFinding]:
        return [
            UniversalFinding(
                id="result-001",
                source="greenbone",
                title="Controlled scanner finding",
                vendor_severity="Medium",
                business_criticality="UNKNOWN",
                asset="192.0.2.10",
                exposed=False,
                detection_available=False,
                threat_intel_match=False,
                mitre_tactic=None,
                owner=None,
                remediation=None,
            )
        ]


class MissingConfigurationQueryService:
    def get_findings(self) -> list[UniversalFinding]:
        raise FindingsConfigurationError(
            "GREENBONE_REPORT_PATH is not configured."
        )


def test_findings_endpoint_returns_minimal_projection_without_legacy_pipeline(
    monkeypatch,
) -> None:
    def fail_legacy_pipeline():
        raise AssertionError("Legacy pipeline must not run.")

    monkeypatch.setattr(api_app.engine, "run", fail_legacy_pipeline)
    response = api_app.findings(StubFindingsQueryService())

    assert [finding.model_dump() for finding in response] == [
        {
            "id": "result-001",
            "source": "greenbone",
            "title": "Controlled scanner finding",
            "vendorSeverity": "Medium",
            "asset": "192.0.2.10",
        }
    ]


def test_findings_endpoint_reports_missing_configuration() -> None:
    with pytest.raises(HTTPException) as captured:
        api_app.findings(MissingConfigurationQueryService())

    assert captured.value.status_code == 503
    assert captured.value.detail == (
        "GREENBONE_REPORT_PATH is not configured."
    )
