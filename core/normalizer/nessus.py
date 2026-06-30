from models import Asset, Software, Vulnerability, NormalizedFinding


def normalize(raw):

    asset = Asset(
        ip=raw.get("host", ""),
        hostname=raw.get("hostname", ""),
        internet_facing=raw.get("internet_facing", False)
    )

    software = Software(
        name=raw.get("software", ""),
        version=raw.get("version", "")
    )

    vulnerability = Vulnerability(
        cve=raw.get("cve"),
        title=raw.get("plugin_name", ""),
        severity=raw.get("severity", "unknown"),
        cvss=float(raw.get("cvss", 0)),
        exploit_available=raw.get("exploit_available", False)
    )

    return NormalizedFinding(
        asset=asset,
        software=software,
        vulnerability=vulnerability,
        source="nessus",
        port=raw.get("port"),
        protocol=raw.get("protocol")
    )
