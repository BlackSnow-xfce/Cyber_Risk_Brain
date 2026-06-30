from core.models import Finding


class WizConnector:

    def get_findings(self):

        findings = [

            Finding(
                name="Wiz Finding",
                severity="CRITICAL",
                exposed=True,
                criticality="CRITICAL",
                detection=False,
                threat_intel=True,
                mitre="Privilege Escalation",
                owner="Cloud Team",
                sla_days=3
            ),

            Finding(
                name="Public S3 Bucket",
                severity="HIGH",
                exposed=True,
                criticality="HIGH",
                detection=True,
                threat_intel=False,
                mitre="Collection",
                owner="Storage Team",
                sla_days=14
            ),

            Finding(
                name="Internal Admin Panel",
                severity="HIGH",
                exposed=False,
                criticality="MEDIUM",
                detection=False,
                threat_intel=False,
                mitre="Lateral Movement",
                owner="Infrastructure Team",
                sla_days=30
            ),

            Finding(
                name="Exposed VM",
                severity="MEDIUM",
                exposed=True,
                criticality="LOW",
                detection=False,
                threat_intel=True,
                mitre="Initial Access",
                owner="Server Team",
                sla_days=21
            )
        ]

        return findings
