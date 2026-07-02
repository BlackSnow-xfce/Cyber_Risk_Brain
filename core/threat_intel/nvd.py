from typing import Iterable, List

from .client import ThreatIntelHTTPClient
from .exceptions import ThreatIntelHTTPError
from .models import ThreatIntelResult
from .providers import ThreatIntelProvider


class NVDProvider(ThreatIntelProvider):

    BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

    def __init__(self, client: ThreatIntelHTTPClient | None = None):
        self.client = client or ThreatIntelHTTPClient(timeout=30)

    def lookup(self, cves: Iterable[str]) -> List[ThreatIntelResult]:

        results: List[ThreatIntelResult] = []

        normalized_cves = sorted({
            cve.strip().upper()
            for cve in cves
            if cve
        })

        for cve in normalized_cves:

            url = f"{self.BASE_URL}?cveId={cve}"

            try:
                response = self.client.get_json(url)

            except ThreatIntelHTTPError:
                continue

            vulnerabilities = response.get("vulnerabilities", [])

            if not vulnerabilities:
                continue

            vuln = vulnerabilities[0]["cve"]

            descriptions = vuln.get("descriptions", [])
            description = next(
                (
                    item.get("value")
                    for item in descriptions
                    if item.get("lang") == "en"
                ),
                None,
            )

            metrics = vuln.get("metrics", {})

            cvss_score = None
            cvss_severity = None
            cvss_version = None
            cvss_vector = None

            attack_vector = None
            attack_complexity = None
            privileges_required = None
            user_interaction = None
            scope = None

            confidentiality = None
            integrity = None
            availability = None

            if "cvssMetricV31" in metrics:

                metric = metrics["cvssMetricV31"][0]
                cvss = metric["cvssData"]

                cvss_score = cvss.get("baseScore")
                cvss_version = cvss.get("version")
                cvss_vector = cvss.get("vectorString")

                cvss_severity = metric.get("baseSeverity")

                attack_vector = cvss.get("attackVector")
                attack_complexity = cvss.get("attackComplexity")
                privileges_required = cvss.get("privilegesRequired")
                user_interaction = cvss.get("userInteraction")
                scope = cvss.get("scope")

                confidentiality = cvss.get("confidentialityImpact")
                integrity = cvss.get("integrityImpact")
                availability = cvss.get("availabilityImpact")

            elif "cvssMetricV30" in metrics:

                metric = metrics["cvssMetricV30"][0]
                cvss = metric["cvssData"]

                cvss_score = cvss.get("baseScore")
                cvss_version = cvss.get("version")
                cvss_vector = cvss.get("vectorString")

                cvss_severity = metric.get("baseSeverity")

                attack_vector = cvss.get("attackVector")
                attack_complexity = cvss.get("attackComplexity")
                privileges_required = cvss.get("privilegesRequired")
                user_interaction = cvss.get("userInteraction")
                scope = cvss.get("scope")

                confidentiality = cvss.get("confidentialityImpact")
                integrity = cvss.get("integrityImpact")
                availability = cvss.get("availabilityImpact")

            elif "cvssMetricV2" in metrics:

                metric = metrics["cvssMetricV2"][0]
                cvss = metric["cvssData"]

                cvss_score = cvss.get("baseScore")
                cvss_version = "2.0"
                cvss_vector = cvss.get("vectorString")

                cvss_severity = metric.get("baseSeverity")

                attack_vector = cvss.get("accessVector")
                attack_complexity = cvss.get("accessComplexity")

                confidentiality = cvss.get("confidentialityImpact")
                integrity = cvss.get("integrityImpact")
                availability = cvss.get("availabilityImpact")

            weaknesses = vuln.get("weaknesses", [])

            cwe = None

            if weaknesses:
                weakness_descriptions = weaknesses[0].get("description", [])

                if weakness_descriptions:
                    cwe = weakness_descriptions[0].get("value")

            result = ThreatIntelResult(
                cve_id=cve,
                description=description,
                published=vuln.get("published"),
                last_modified=vuln.get("lastModified"),
                cvss_score=cvss_score,
                cvss_severity=cvss_severity,
                cvss_version=cvss_version,
                cvss_vector=cvss_vector,
                attack_vector=attack_vector,
                attack_complexity=attack_complexity,
                privileges_required=privileges_required,
                user_interaction=user_interaction,
                scope=scope,
                confidentiality=confidentiality,
                integrity=integrity,
                availability=availability,
                cwe=cwe,
            )

            result.add_source(
                name="NVD",
                available=True,
                data=vulnerabilities[0],
            )

            results.append(result)

        return results
