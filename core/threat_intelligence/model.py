from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Generic, TypeVar

from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)

THREAT_INTELLIGENCE_CONTRACT_VERSION = "1.0"
_CVE_PATTERN = re.compile(r"^CVE-[0-9]{4}-[0-9]{4,}$")
_FactValue = TypeVar("_FactValue")


class ThreatIntelligenceSource(StrEnum):
    NVD = "nvd"
    EPSS = "epss"
    CISA_KEV = "cisa_kev"


class FindingIntelligenceApplicability(StrEnum):
    APPLICABLE = "applicable"
    NOT_APPLICABLE = "not_applicable"
    NOT_EVALUATED = "not_evaluated"


@dataclass(frozen=True, slots=True)
class CveIdentifier:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().upper()
        if not _CVE_PATTERN.fullmatch(normalized):
            raise ValueError("CVE identifier must use the canonical CVE format.")
        object.__setattr__(self, "value", normalized)


@dataclass(frozen=True, slots=True)
class IntelligenceFact(Generic[_FactValue]):
    value: _FactValue | None
    completeness: ExplanationCompleteness
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        available = self.completeness.status == CompletenessStatus.AVAILABLE
        if available and self.value is None:
            raise ValueError("Available intelligence must contain a value.")
        if not available and self.value is not None:
            raise ValueError(
                "Unavailable intelligence must not contain a sentinel value."
            )
        if (
            self.observed_at is not None
            and self.observed_at.utcoffset() is None
        ):
            raise ValueError("Intelligence timestamps must include a timezone.")

    @property
    def provenance(self) -> ExplanationProvenance:
        return self.completeness.provenance


@dataclass(frozen=True, slots=True)
class NvdIntelligence:
    summary: str | None = None
    published_at: datetime | None = None
    last_modified_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.summary is not None and not self.summary.strip():
            raise ValueError("NVD summary must not be empty.")
        if (
            self.summary is None
            and self.published_at is None
            and self.last_modified_at is None
        ):
            raise ValueError("NVD intelligence must contain source data.")
        _require_timezone(self.published_at, "NVD published timestamp")
        _require_timezone(self.last_modified_at, "NVD modified timestamp")


@dataclass(frozen=True, slots=True)
class CvssInformation:
    version: str
    base_score: float
    vector: str
    severity: str | None = None

    def __post_init__(self) -> None:
        if not self.version.strip():
            raise ValueError("CVSS version must not be empty.")
        if not 0 <= self.base_score <= 10:
            raise ValueError("CVSS base score must be between 0 and 10.")
        if not self.vector.strip():
            raise ValueError("CVSS vector must not be empty.")
        if self.severity is not None and not self.severity.strip():
            raise ValueError("CVSS severity must not be empty.")


@dataclass(frozen=True, slots=True)
class EpssInformation:
    probability: float
    percentile: float | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.probability <= 1:
            raise ValueError("EPSS probability must be between 0 and 1.")
        if self.percentile is not None and not 0 <= self.percentile <= 1:
            raise ValueError("EPSS percentile must be between 0 and 1.")


@dataclass(frozen=True, slots=True)
class CisaKevInformation:
    known_exploited: bool
    date_added: date | None = None
    required_action: str | None = None
    due_date: date | None = None

    def __post_init__(self) -> None:
        if self.required_action is not None and not self.required_action.strip():
            raise ValueError("CISA KEV required action must not be empty.")
        if not self.known_exploited and any(
            value is not None
            for value in (self.date_added, self.required_action, self.due_date)
        ):
            raise ValueError(
                "A vulnerability absent from CISA KEV must not contain KEV fields."
            )


@dataclass(frozen=True, slots=True)
class ExploitationEvidence:
    evidence_type: str
    description: str
    provenance: ExplanationProvenance
    observed_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.evidence_type.strip():
            raise ValueError("Exploitation evidence type must not be empty.")
        if not self.description.strip():
            raise ValueError("Exploitation evidence description must not be empty.")
        _require_timezone(self.observed_at, "Evidence observation timestamp")


@dataclass(frozen=True, slots=True)
class VulnerabilityThreatIntelligence:
    cve_identifier: CveIdentifier
    nvd: IntelligenceFact[NvdIntelligence]
    cvss: IntelligenceFact[CvssInformation]
    epss: IntelligenceFact[EpssInformation]
    cisa_kev: IntelligenceFact[CisaKevInformation]
    exploitation_evidence: IntelligenceFact[tuple[ExploitationEvidence, ...]]
    contract_version: str = THREAT_INTELLIGENCE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        if not self.contract_version.strip():
            raise ValueError("Threat intelligence contract version must not be empty.")
        _require_source(self.nvd, ThreatIntelligenceSource.NVD, "NVD")
        _require_source(self.cvss, ThreatIntelligenceSource.NVD, "CVSS")
        _require_source(self.epss, ThreatIntelligenceSource.EPSS, "EPSS")
        _require_source(
            self.cisa_kev,
            ThreatIntelligenceSource.CISA_KEV,
            "CISA KEV",
        )
        evidence = self.exploitation_evidence.value
        if evidence is not None and not evidence:
            raise ValueError(
                "Available exploitation evidence must contain at least one item."
            )


@dataclass(frozen=True, slots=True)
class FindingThreatIntelligence:
    finding_id: str
    applicability: FindingIntelligenceApplicability
    vulnerability: VulnerabilityThreatIntelligence | None = None

    def __post_init__(self) -> None:
        if not self.finding_id.strip():
            raise ValueError("Finding ID must not be empty.")
        if self.applicability == FindingIntelligenceApplicability.APPLICABLE:
            if self.vulnerability is None:
                raise ValueError(
                    "Applicable finding intelligence requires a vulnerability."
                )
        elif self.vulnerability is not None:
            raise ValueError(
                "Non-applicable or unevaluated findings must not contain a CVE."
            )


def _require_timezone(value: datetime | None, label: str) -> None:
    if value is not None and value.utcoffset() is None:
        raise ValueError(f"{label} must include a timezone.")


def _require_source(
    fact: IntelligenceFact[object],
    source: ThreatIntelligenceSource,
    label: str,
) -> None:
    if fact.provenance.source_type != source.value:
        raise ValueError(f"{label} intelligence must retain source provenance.")
