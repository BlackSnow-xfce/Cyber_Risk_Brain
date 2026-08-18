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
    assert finding.cve_identifiers == (
        "CVE-2021-44228",
        "CVE-2024-12345",
    )


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


def test_maps_cve_reference_embedded_in_greenbone_nvt_name() -> None:
    report = b"""\
<report>
  <results>
    <result id="6d3167e9-002c-4b76-a5a7-ce47f81b78b1">
      <host>172.18.0.19</host>
      <nvt oid="1.3.6.1.4.1.25623.1.0.103553">
        <name>DistCC RCE Vulnerability (CVE-2004-2687)</name>
        <refs>
          <ref type="dfn-cert" id="DFN-CERT-2019-0381" />
        </refs>
      </nvt>
      <threat>Critical</threat>
    </result>
  </results>
</report>
"""

    finding = parse_greenbone_xml_findings(report)[0]

    assert finding.cve_identifiers == ("CVE-2004-2687",)
