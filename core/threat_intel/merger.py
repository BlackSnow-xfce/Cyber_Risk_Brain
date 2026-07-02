from typing import Dict, Iterable, List

from .models import ThreatIntelResult


class ThreatIntelMerger:

    def merge_many(
        self,
        cves: Iterable[str],
        partial_results: Iterable[ThreatIntelResult],
    ) -> Dict[str, ThreatIntelResult]:

        merged: Dict[str, ThreatIntelResult] = {}

        normalized_cves = sorted({
            cve.strip().upper()
            for cve in cves
            if cve
        })

        for cve in normalized_cves:
            merged[cve] = ThreatIntelResult(cve_id=cve)

        for result in partial_results:
            cve = result.cve_id.upper()

            if cve not in merged:
                merged[cve] = ThreatIntelResult(cve_id=cve)

            self.merge(merged[cve], result)

        return merged

    def merge(
        self,
        current: ThreatIntelResult,
        incoming: ThreatIntelResult,
    ) -> ThreatIntelResult:

        if incoming.epss_score is not None:
            current.epss_score = incoming.epss_score

        if incoming.epss_percentile is not None:
            current.epss_percentile = incoming.epss_percentile

        if incoming.is_kev:
            current.is_kev = True

        if incoming.kev_vendor_project:
            current.kev_vendor_project = incoming.kev_vendor_project

        if incoming.kev_product:
            current.kev_product = incoming.kev_product

        if incoming.kev_vulnerability_name:
            current.kev_vulnerability_name = incoming.kev_vulnerability_name

        if incoming.kev_date_added:
            current.kev_date_added = incoming.kev_date_added

        if incoming.kev_short_description:
            current.kev_short_description = incoming.kev_short_description

        if incoming.kev_required_action:
            current.kev_required_action = incoming.kev_required_action

        if incoming.kev_due_date:
            current.kev_due_date = incoming.kev_due_date

        if incoming.kev_known_ransomware_campaign_use:
            current.kev_known_ransomware_campaign_use = (
                incoming.kev_known_ransomware_campaign_use
            )

        if incoming.kev_notes:
            current.kev_notes = incoming.kev_notes

        if incoming.exploit_available is not None:
            current.exploit_available = incoming.exploit_available

        if incoming.exploitation_observed is not None:
            current.exploitation_observed = incoming.exploitation_observed

        if incoming.ransomware_usage_observed is not None:
            current.ransomware_usage_observed = incoming.ransomware_usage_observed

        current.sources.extend(incoming.sources)

        return current
