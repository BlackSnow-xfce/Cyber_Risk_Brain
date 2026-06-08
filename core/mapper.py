from core.models import UniversalFinding


def finding_to_universal(finding):

    return UniversalFinding(
        id=finding.name.lower().replace(" ", "_"),
        source="wiz",
        title=finding.name,
        vendor_severity=finding.severity,
        business_criticality=finding.criticality,
        asset=finding.name,
        exposed=finding.exposed,
        detection_available=finding.detection,
        threat_intel_match=finding.threat_intel,
        mitre_tactic=finding.mitre,
        owner=finding.owner,
        remediation=None
    )