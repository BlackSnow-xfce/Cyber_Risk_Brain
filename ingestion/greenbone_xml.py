from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from core.models import UniversalFinding

GREENBONE_SOURCE = "greenbone"


def load_greenbone_xml_findings(
    report_path: str | Path,
) -> list[UniversalFinding]:
    """Load findings from one Greenbone GMP XML report export."""

    return parse_greenbone_xml_findings(
        Path(report_path).read_bytes()
    )


def parse_greenbone_xml_findings(
    report_xml: str | bytes,
) -> list[UniversalFinding]:
    """Map Greenbone GMP XML result records to canonical findings."""

    _reject_document_type(report_xml)

    try:
        root = ElementTree.fromstring(report_xml)
    except ElementTree.ParseError as error:
        raise ValueError("Invalid Greenbone XML report.") from error

    result_elements = [
        element
        for element in root.iter()
        if _local_name(element.tag) == "result"
    ]

    if not result_elements:
        raise ValueError("Greenbone XML report contains no results.")

    return [
        _map_result(result)
        for result in result_elements
    ]


def _map_result(
    result: ElementTree.Element,
) -> UniversalFinding:
    result_id = _required_attribute(
        result,
        "id",
        "Greenbone result ID",
    )
    host = _required_child_text(
        result,
        "host",
        "Greenbone result host",
    )
    nvt = _required_child(
        result,
        "nvt",
        "Greenbone result NVT",
    )
    title = _required_child_text(
        nvt,
        "name",
        "Greenbone NVT name",
    )
    vendor_severity = (
        _child_text(result, "threat")
        or _child_text(result, "severity")
    )

    if vendor_severity is None:
        raise ValueError(
            "Greenbone result threat or severity must not be empty."
        )

    return UniversalFinding(
        id=result_id,
        source=GREENBONE_SOURCE,
        title=title,
        vendor_severity=vendor_severity,
        business_criticality="UNKNOWN",
        asset=host,
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
    )


def _required_attribute(
    element: ElementTree.Element,
    attribute: str,
    label: str,
) -> str:
    value = element.get(attribute, "").strip()

    if not value:
        raise ValueError(f"{label} must not be empty.")

    return value


def _required_child(
    element: ElementTree.Element,
    child_name: str,
    label: str,
) -> ElementTree.Element:
    for child in element:
        if _local_name(child.tag) == child_name:
            return child

    raise ValueError(f"{label} must not be empty.")


def _required_child_text(
    element: ElementTree.Element,
    child_name: str,
    label: str,
) -> str:
    value = _child_text(element, child_name)

    if value is None:
        raise ValueError(f"{label} must not be empty.")

    return value


def _child_text(
    element: ElementTree.Element,
    child_name: str,
) -> str | None:
    for child in element:
        if _local_name(child.tag) != child_name:
            continue

        value = (child.text or "").strip()
        return value or None

    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _reject_document_type(report_xml: str | bytes) -> None:
    marker = (
        report_xml.upper()
        if isinstance(report_xml, bytes)
        else report_xml.upper().encode("utf-8")
    )

    if b"<!DOCTYPE" in marker or b"<!ENTITY" in marker:
        raise ValueError(
            "Greenbone XML report must not contain a document type."
        )
