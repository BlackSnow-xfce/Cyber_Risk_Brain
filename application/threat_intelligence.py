from __future__ import annotations

from typing import Protocol

from core.threat_intelligence import (
    CveIdentifier,
    VulnerabilityThreatIntelligence,
)


class ThreatIntelligenceConfigurationError(RuntimeError):
    """Raised when no productive threat-intelligence reader is configured."""


class ThreatIntelligenceNotFoundError(LookupError):
    """Raised when a configured reader has no record for one CVE."""


class ThreatIntelligenceDataError(ValueError):
    """Raised when a reader violates the canonical read contract."""


class ThreatIntelligenceSourceUnavailableError(RuntimeError):
    """Raised when the configured intelligence source cannot be reached."""


class ThreatIntelligenceTimeoutError(TimeoutError):
    """Raised when the configured intelligence source times out."""


class ThreatIntelligenceInvalidResponseError(ValueError):
    """Raised when a source response cannot satisfy the read contract."""


class ThreatIntelligenceReader(Protocol):
    def get_by_cve(
        self,
        cve_identifier: CveIdentifier,
    ) -> VulnerabilityThreatIntelligence | None: ...


class ThreatIntelligenceQueryService:
    """Read canonical vulnerability intelligence without evaluating risk."""

    def __init__(self, reader: ThreatIntelligenceReader | None) -> None:
        self._reader = reader

    def get_by_cve(self, cve: str) -> VulnerabilityThreatIntelligence:
        cve_identifier = CveIdentifier(cve)
        if self._reader is None:
            raise ThreatIntelligenceConfigurationError(
                "Threat intelligence source is not configured."
            )

        intelligence = self._reader.get_by_cve(cve_identifier)
        if intelligence is None:
            raise ThreatIntelligenceNotFoundError(
                "Threat intelligence was not found."
            )
        if intelligence.cve_identifier != cve_identifier:
            raise ThreatIntelligenceDataError(
                "Threat intelligence reader returned a different CVE."
            )
        return intelligence
