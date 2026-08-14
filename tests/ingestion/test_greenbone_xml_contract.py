from pathlib import Path

from ingestion import (
    load_greenbone_xml_findings,
    parse_greenbone_xml_findings,
)


GREENBONE_XML_SCHEMA_SAMPLE = (
    Path(__file__).parent
    / "fixtures"
    / "greenbone-gmp-schema-sample.xml"
)


def test_maps_greenbone_result_to_existing_canonical_finding() -> None:
    findings = parse_greenbone_xml_findings(
        GREENBONE_XML_SCHEMA_SAMPLE.read_bytes()
    )

    assert len(findings) == 1
    finding = findings[0]
    assert finding.id == "51d5d153-5f01-4da9-83d5-e17c47bb69a5"
    assert finding.source == "greenbone"
    assert finding.title == "HTTP Security Header Detection"
    assert finding.vendor_severity == "High"
    assert finding.asset == "192.0.2.10"
    assert finding.business_criticality == "UNKNOWN"
    assert finding.exposed is False
    assert finding.detection_available is False
    assert finding.threat_intel_match is False
    assert finding.mitre_tactic is None
    assert finding.owner is None
    assert finding.remediation is None


def test_greenbone_mapping_is_deterministic() -> None:
    first = parse_greenbone_xml_findings(
        GREENBONE_XML_SCHEMA_SAMPLE.read_bytes()
    )
    second = parse_greenbone_xml_findings(
        GREENBONE_XML_SCHEMA_SAMPLE.read_bytes()
    )

    assert first == second


def test_file_boundary_preserves_greenbone_source_identity() -> None:
    finding = load_greenbone_xml_findings(
        GREENBONE_XML_SCHEMA_SAMPLE
    )[0]

    assert (
        finding.source,
        finding.id,
    ) == (
        "greenbone",
        "51d5d153-5f01-4da9-83d5-e17c47bb69a5",
    )
