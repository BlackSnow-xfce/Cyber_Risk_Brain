from typing import Dict, Iterable, List

from .merger import ThreatIntelMerger
from .models import ThreatIntelResult
from .providers import ThreatIntelProvider


class ThreatIntelService:

    def __init__(
        self,
        providers: List[ThreatIntelProvider] | None = None,
        merger: ThreatIntelMerger | None = None,
    ):
        self.providers = providers or []
        self.merger = merger or ThreatIntelMerger()

    def lookup(self, cves: Iterable[str]) -> Dict[str, ThreatIntelResult]:

        normalized_cves = sorted({
            cve.strip().upper()
            for cve in cves
            if cve
        })

        partial_results: List[ThreatIntelResult] = []

        for provider in self.providers:
            partial_results.extend(provider.lookup(normalized_cves))

        return self.merger.merge_many(
            cves=normalized_cves,
            partial_results=partial_results,
        )
