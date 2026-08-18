from __future__ import annotations

from dataclasses import dataclass

from application.finding_explanation_use_case import (
    FindingNotFoundError,
    FindingSelectionError,
)
from application.findings_query import FindingsQueryService
from application.threat_intelligence import (
    ThreatIntelligenceDataError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceReader,
)
from core.threat_intelligence import (
    CveIdentifier,
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
)


@dataclass(frozen=True, slots=True)
class FindingThreatIntelligenceEnrichment:
    finding_id: str
    finding_source: str
    finding_title: str
    relationships: tuple[FindingThreatIntelligence, ...]


class FindingThreatIntelligenceUseCase:
    """Relate one live finding to canonical TI without evaluating risk."""

    def __init__(
        self,
        findings: FindingsQueryService,
        reader: ThreatIntelligenceReader,
    ) -> None:
        self._findings = findings
        self._reader = reader

    def enrich(self, finding_id: str) -> FindingThreatIntelligenceEnrichment:
        matches = [
            finding
            for finding in self._findings.get_findings()
            if finding.id == finding_id
        ]
        if not matches:
            raise FindingNotFoundError(finding_id)
        if len(matches) > 1:
            raise FindingSelectionError(
                "Configured finding source contains a duplicate finding ID."
            )

        finding = matches[0]
        cve_identifiers = tuple(
            dict.fromkeys(
                CveIdentifier(value)
                for value in finding.cve_identifiers
            )
        )
        if not cve_identifiers:
            relationships = (
                FindingThreatIntelligence(
                    finding_id=finding.id,
                    applicability=(
                        FindingIntelligenceApplicability.NOT_APPLICABLE
                    ),
                ),
            )
        else:
            relationships = tuple(
                self._relationship(finding.id, cve_identifier)
                for cve_identifier in cve_identifiers
            )

        return FindingThreatIntelligenceEnrichment(
            finding_id=finding.id,
            finding_source=finding.source,
            finding_title=finding.title,
            relationships=relationships,
        )

    def _relationship(
        self,
        finding_id: str,
        cve_identifier: CveIdentifier,
    ) -> FindingThreatIntelligence:
        intelligence = self._reader.get_by_cve(cve_identifier)
        if intelligence is None:
            raise ThreatIntelligenceNotFoundError(
                "Threat intelligence was not found."
            )
        if intelligence.cve_identifier != cve_identifier:
            raise ThreatIntelligenceDataError(
                "Threat intelligence reader returned a different CVE."
            )
        return FindingThreatIntelligence(
            finding_id=finding_id,
            applicability=FindingIntelligenceApplicability.APPLICABLE,
            vulnerability=intelligence,
        )
