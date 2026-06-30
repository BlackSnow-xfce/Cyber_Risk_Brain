from normalizer.nessus import normalize
from asset_resolver import AssetResolver

raw1 = {
    "host": "10.0.0.5",
    "hostname": "Server01",
    "internet_facing": True,
    "software": "Apache",
    "version": "2.4.48",
    "cve": "CVE-2025-1234",
    "plugin_name": "Apache RCE",
    "severity": "critical",
    "cvss": 9.8,
    "exploit_available": True,
    "port": 443,
    "protocol": "tcp"
}

raw2 = {
    "host": "10.0.0.5",
    "hostname": "Server01",
    "software": "OpenSSH",
    "version": "8.2",
    "cve": "CVE-2024-6387",
    "plugin_name": "OpenSSH regreSSHion",
    "severity": "high",
    "cvss": 8.1,
    "exploit_available": False,
    "port": 22,
    "protocol": "tcp"
}

raw3 = {
    "host": "10.0.0.8",
    "hostname": "Fileserver",
    "software": "SMB",
    "plugin_name": "SMB Signing Disabled",
    "severity": "medium",
    "cvss": 5.3,
    "port": 445,
    "protocol": "tcp"
}

findings = [
    normalize(raw1),
    normalize(raw2),
    normalize(raw3)
]

resolver = AssetResolver()

assets = resolver.resolve(findings)

for asset, asset_findings in assets.items():

    print("=" * 50)

    print(asset)

    print(f"Findings: {len(asset_findings)}")

    for finding in asset_findings:

        print(
            finding.vulnerability.title,
            finding.vulnerability.severity
        )
