from core.explainability import CompletenessStatus
from core.threat_intelligence import FindingIntelligenceApplicability
from application.finding_threat_intelligence import FindingThreatIntelligenceEnrichment
from application.security_observation_correlation import SecurityObservationCorrelationResult


class ThreatIntelligencePromoter:
    def promote(self, enrichment: FindingThreatIntelligenceEnrichment, correlation: SecurityObservationCorrelationResult, *, finding_id: str, asset_reference: str) -> bool | None:
        if enrichment.finding_id != finding_id or correlation.finding_id != finding_id or correlation.completeness.status is not CompletenessStatus.AVAILABLE: return None
        for relationship in enrichment.relationships:
            if relationship.applicability is not FindingIntelligenceApplicability.APPLICABLE or relationship.vulnerability is None: return None
            cve = relationship.vulnerability.cve_identifier.value
            evidence = next((item for item in correlation.evidence if item.identifier == f"correlation:{finding_id}:{cve}"), None)
            if evidence is None or evidence.provenance is None: return None
            refs = evidence.provenance.input_references
            if asset_reference not in refs or not any(ref.startswith("finding:") and ref.endswith(f":{finding_id}") for ref in refs): return None
        return bool(enrichment.relationships)
