from __future__ import annotations

from dataclasses import dataclass

from core.decision.models import (
    Evidence,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceType,
)
from core.enterprise_context import AssetContext
from core.explainability import CompletenessStatus
from core.threat_intelligence import FindingThreatIntelligence

CORRELATION_EVIDENCE_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class SecurityObservationCorrelationInput:
    finding_id: str
    finding_source: str
    asset_context: AssetContext
    threat_intelligence: FindingThreatIntelligence

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Correlation finding ID must not be empty.")
        if not self.finding_source.strip():
            raise ValueError("Correlation finding source must not be empty.")
        if self.threat_intelligence.finding_id != self.finding_id:
            raise ValueError(
                "Correlation inputs must reference the same finding."
            )


class SecurityObservationCorrelationService:
    """Create deterministic correlation evidence without risk semantics."""

    def correlate(
        self,
        correlation_input: SecurityObservationCorrelationInput,
    ) -> Evidence:
        vulnerability = correlation_input.threat_intelligence.vulnerability
        if vulnerability is None:
            raise ValueError(
                "Correlation requires applicable threat intelligence."
            )
        if any(
            fact.completeness.status is not CompletenessStatus.AVAILABLE
            for fact in (
                vulnerability.nvd,
                vulnerability.cvss,
                vulnerability.epss,
                vulnerability.cisa_kev,
            )
        ):
            raise ValueError(
                "Correlation requires available authoritative TI facts."
            )

        cve = vulnerability.cve_identifier.value
        finding_reference = (
            f"finding:{correlation_input.finding_source}:"
            f"{correlation_input.finding_id}"
        )
        asset_reference = (
            f"asset-context:{correlation_input.asset_context.canonical_asset_id}:"
            f"{correlation_input.asset_context.source_reference}"
        )
        intelligence_references = tuple(
            f"threat-intelligence:{cve}:{name}:"
            f"{fact.provenance.source_reference}"
            for name, fact in (
                ("nvd", vulnerability.nvd),
                ("cvss", vulnerability.cvss),
                ("epss", vulnerability.epss),
                ("cisa-kev", vulnerability.cisa_kev),
            )
        )

        return Evidence(
            evidence_type=EvidenceType.CORRELATION,
            key="finding-cve-canonical-asset-correlation",
            value=(
                f"Finding {correlation_input.finding_id} references {cve} "
                "and its observed asset resolves to canonical asset "
                f"{correlation_input.asset_context.canonical_asset_id}; "
                "NVD, CVSS, EPSS, and CISA KEV facts are available."
            ),
            source="security_observation_correlation",
            description=(
                "Deterministic association of an observed finding, its CVE "
                "intelligence, and explicit canonical asset context."
            ),
            identifier=(
                f"correlation:{correlation_input.finding_id}:{cve}"
            ),
            kind=EvidenceKind.DERIVED,
            provenance=EvidenceProvenance(
                source_type="security_observation_correlation",
                source_reference=(
                    "security-observation-correlation:1.0:"
                    f"{correlation_input.finding_id}:{cve}"
                ),
                input_references=(
                    finding_reference,
                    asset_reference,
                    *intelligence_references,
                ),
            ),
            contract_version=CORRELATION_EVIDENCE_CONTRACT_VERSION,
        )
