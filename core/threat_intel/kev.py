from typing import Iterable, List

from .client import ThreatIntelHTTPClient
from .models import ThreatIntelResult
from .providers import ThreatIntelProvider


class KEVProvider(ThreatIntelProvider):

    URL = (
        "https://www.cisa.gov/sites/default/files/feeds/"
        "known_exploited_vulnerabilities.json"
    )

    def __init__(self, client: ThreatIntelHTTPClient | None = None):
        self.client = client or ThreatIntelHTTPClient()

    def lookup(self, cves: Iterable[str]) -> List[ThreatIntelResult]:

        normalized_cves = {
            cve.strip().upper()
            for cve in cves
            if cve
        }

        if not normalized_cves:
            return []

        response = self.client.get_json(self.URL)

        vulnerabilities = response.get("vulnerabilities", [])

        results: List[ThreatIntelResult] = []

        for item in vulnerabilities:

            cve = item.get("cveID", "").upper()

            if cve not in normalized_cves:
                continue

            result = ThreatIntelResult(
                cve_id=cve,
                is_kev=True,
            )

            result.kev_vendor_project = item.get("vendorProject")
            result.kev_product = item.get("product")
            result.kev_vulnerability_name = item.get("vulnerabilityName")
            result.kev_date_added = item.get("dateAdded")
            result.kev_short_description = item.get("shortDescription")
            result.kev_required_action = item.get("requiredAction")
            result.kev_due_date = item.get("dueDate")
            result.kev_known_ransomware_campaign_use = (
                item.get("knownRansomwareCampaignUse")
            )
            result.kev_notes = item.get("notes")

            result.exploitation_observed = True

            result.ransomware_usage_observed = (
                str(item.get("knownRansomwareCampaignUse", ""))
                .strip()
                .lower()
                == "known"
            )

            result.add_source(
                name="CISA KEV",
                available=True,
                data=item,
            )

            results.append(result)

        return results
