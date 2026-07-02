from typing import Iterable, List

from .client import ThreatIntelHTTPClient
from .models import ThreatIntelResult
from .providers import ThreatIntelProvider


class EPSSProvider(ThreatIntelProvider):

    BASE_URL = "https://api.first.org/data/v1/epss"

    def __init__(self, client: ThreatIntelHTTPClient | None = None):
        self.client = client or ThreatIntelHTTPClient()

    def lookup(self, cves: Iterable[str]) -> List[ThreatIntelResult]:

        normalized_cves = sorted({
            cve.strip().upper()
            for cve in cves
            if cve
        })

        if not normalized_cves:
            return []

        url = (
            f"{self.BASE_URL}"
            f"?cve={','.join(normalized_cves)}"
        )

        response = self.client.get_json(url)

        results: List[ThreatIntelResult] = []

        for item in response.get("data", []):

            cve = item.get("cve", "").upper()
            epss = item.get("epss")
            percentile = item.get("percentile")

            if not cve:
                continue

            result = ThreatIntelResult(
                cve_id=cve,
                epss_score=float(epss) if epss is not None else None,
                epss_percentile=float(percentile)
                if percentile is not None else None,
            )

            result.add_source(
                name="EPSS",
                available=True,
                data={
                    "epss": epss,
                    "percentile": percentile,
                },
            )

            results.append(result)

        return results
