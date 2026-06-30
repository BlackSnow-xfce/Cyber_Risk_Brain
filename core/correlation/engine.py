from models import NormalizedFinding


class CorrelationEngine:

    def analyze(self, finding: NormalizedFinding):

        score = 0
        reasons = []

        # Internet Facing
        if finding.asset.internet_facing:
            score += 20
            reasons.append("Asset is internet-facing.")

        # Critical Severity
        if finding.vulnerability.severity.lower() == "critical":
            score += 30
            reasons.append("Critical vulnerability detected.")

        # Public Exploit
        if finding.vulnerability.exploit_available:
            score += 25
            reasons.append("Public exploit available.")

        # High CVSS
        if finding.vulnerability.cvss >= 9.0:
            score += 15
            reasons.append("CVSS >= 9.0")

        score = min(score, 100)

        return {
            "asset": finding.asset.hostname or finding.asset.ip,
            "score": score,
            "reasons": reasons
        }
