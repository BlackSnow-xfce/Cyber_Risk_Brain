from pathlib import Path

import pytest

from application import FindingsConfigurationError, FindingsQueryService


GREENBONE_XML_SCHEMA_SAMPLE = (
    Path(__file__).parents[1]
    / "ingestion"
    / "fixtures"
    / "greenbone-gmp-schema-sample.xml"
)


def test_loads_findings_through_existing_greenbone_boundary() -> None:
    findings = FindingsQueryService(
        str(GREENBONE_XML_SCHEMA_SAMPLE)
    ).get_findings()

    assert len(findings) == 1
    assert findings[0].source == "greenbone"
    assert findings[0].title == "HTTP Security Header Detection"


@pytest.mark.parametrize("report_path", [None, "", "  "])
def test_rejects_missing_report_path(report_path: str | None) -> None:
    with pytest.raises(
        FindingsConfigurationError,
        match="GREENBONE_REPORT_PATH",
    ):
        FindingsQueryService(report_path).get_findings()


def test_rejects_missing_report_file() -> None:
    report_path = GREENBONE_XML_SCHEMA_SAMPLE.with_name(
        "missing-greenbone-report.xml"
    )

    with pytest.raises(FileNotFoundError):
        FindingsQueryService(str(report_path)).get_findings()
