from typing import Dict, Iterable, List

from .models import ThreatIntelResult
from .providers import ThreatIntelProvider


class ThreatIntelService:

    def __init__(self, providers: List[ThreatIntelProvider] | None = None):
        self.providers = providers or []

    def lookup(self, cves: Iterable[str]) -> Dict[str, ThreatIntelResult]:
        results: Dict[str, ThreatIntelResult] = {}

        normalized_cves = sorted({
            cve.strip().upper()
            for cve in cves
            if cve
        })

        for cve in normalized_cves:
            results[cve] = ThreatIntelResult(cve=cve)

        for provider in self.providers:
            provider_results = provider.lookup(normalized_cves)

            for provider_result in provider_results:
                cve = provider_result.cve.upper()

                if cve not in results:
                    results[cve] = ThreatIntelResult(cve=cve)

                current = results[cve]

                if provider_result.epss_score is not None:
                    current.epss_score = provider_result.epss_score

                if provider_result.epss_percentile is not None:
                    current.epss_percentile = provider_result.epss_percentile

                if provider_result.known_exploited:
                    current.known_exploited = True

                if provider_result.exploit_available:
                    current.exploit_available = True

                current.sources = sorted(set(
                    current.sources + provider_result.sources
                ))

        return results
