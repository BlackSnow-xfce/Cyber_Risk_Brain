from __future__ import annotations

from dataclasses import dataclass

from core.ai_authorization import AIResourceReference
from core.decision.models import (
    Evidence,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceType,
)
from core.enterprise_context import AssetContext
from core.explainability import CompletenessStatus
from core.threat_intelligence import FindingThreatIntelligence
from core.security_observation.observation import (
    SECURITY_OBSERVATION_CONTRACT_VERSION,
    SecurityObservation,
    SecurityObservationIndependence,
    SecurityObservationProvenance,
    SecurityObservationType,
)

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


@dataclass(frozen=True, slots=True)
class SecurityObservationNetworkTrafficCorrelationInput:
    """Explicit contract for deriving evidence from one observation."""

    observation: SecurityObservation
    observation_id: str
    target_resource: AIResourceReference
    observation_type: SecurityObservationType
    independence: SecurityObservationIndependence
    provenance: SecurityObservationProvenance
    contract_version: str = SECURITY_OBSERVATION_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.observation, SecurityObservation):
            raise ValueError("Observation correlation requires an observation.")
        if not isinstance(self.target_resource, AIResourceReference):
            raise ValueError("Observation correlation target must be canonical.")
        if self.observation_id != self.observation.observation_id:
            raise ValueError("Observation ID does not match the observation.")
        if self.target_resource != self.observation.target_resource:
            raise ValueError("Observation target binding does not match.")
        if self.observation_type is not self.observation.observation_type:
            raise ValueError("Observation type does not match the observation.")
        if self.independence is not self.observation.independence:
            raise ValueError("Observation independence does not match.")
        if self.provenance != self.observation.provenance:
            raise ValueError("Observation provenance does not match.")
        if self.contract_version != SECURITY_OBSERVATION_CONTRACT_VERSION:
            raise ValueError(
                "Observation correlation requires SecurityObservation 1.0."
            )


class SecurityObservationCorrelationService:
    """Create deterministic correlation evidence without risk semantics."""

    def correlate_network_traffic(
        self,
        correlation_input: SecurityObservationNetworkTrafficCorrelationInput,
    ) -> Evidence:
        """Derive bounded evidence from one typed network observation.

        Opaque provenance references are retained as references only; this rule
        deliberately does not parse them into additional network facts.
        """
        if not isinstance(
            correlation_input,
            SecurityObservationNetworkTrafficCorrelationInput,
        ):
            raise ValueError("Network correlation input must be canonical.")
        if (
            correlation_input.observation_type
            is not SecurityObservationType.NETWORK_TRAFFIC
        ):
            raise ValueError(
                "Only NETWORK_TRAFFIC observations are supported."
            )

        observation = correlation_input.observation
        input_references = [
            f"observation:{observation.observation_id}",
            (
                "resource:"
                f"{observation.target_resource.resource_type.value}:"
                f"{observation.target_resource.resource_id}"
            ),
            (
                "observation-provenance:"
                f"{observation.provenance.source_type}:"
                f"{observation.provenance.source_reference}"
            ),
        ]
        if observation.provenance.raw_observation_reference is not None:
            input_references.append(
                "observation-raw:"
                f"{observation.provenance.raw_observation_reference}"
            )

        return Evidence(
            evidence_type=EvidenceType.CORRELATION,
            key="security-observation-network-traffic",
            value=(
                "Network traffic was observed for bound resource "
                f"{observation.target_resource.resource_id}."
            ),
            source="security_observation_correlation",
            description=(
                "Deterministic derived evidence from a typed SecurityObservation."
            ),
            identifier=(
                "correlation:security-observation:"
                f"{observation.observation_id}"
            ),
            kind=EvidenceKind.DERIVED,
            provenance=EvidenceProvenance(
                source_type="security_observation_correlation",
                source_reference=(
                    "security-observation-correlation:1.0:"
                    f"{observation.observation_id}"
                ),
                input_references=tuple(input_references),
            ),
            contract_version=CORRELATION_EVIDENCE_CONTRACT_VERSION,
        )

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
