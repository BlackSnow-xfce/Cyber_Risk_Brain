from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from application.finding_threat_intelligence import FindingThreatIntelligenceEnrichment
from core.explainability import CompletenessStatus, ExplanationCompleteness, ExplanationProvenance
from core.threat_intelligence import FindingIntelligenceApplicability


class TechnicalEffectLevel(StrEnum):
    NONE = "NONE"
    LOW = "LOW"
    HIGH = "HIGH"


class FindingTechnicalEffectStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class FindingTechnicalEffect:
    finding_id: str
    cve_identifier: str
    cvss_vector: str
    confidentiality: TechnicalEffectLevel
    integrity: TechnicalEffectLevel
    availability: TechnicalEffectLevel
    source_reference: str
    observed_at: datetime | None

    def __post_init__(self) -> None:
        for name in ("finding_id", "cve_identifier", "cvss_vector", "source_reference"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip():
                raise ValueError(f"Technical effect {name} is invalid.")
        for name in ("confidentiality", "integrity", "availability"):
            if not isinstance(getattr(self, name), TechnicalEffectLevel):
                raise ValueError(f"Technical effect {name} is invalid.")
        if self.observed_at is not None and self.observed_at.utcoffset() is None:
            raise ValueError("Technical effect observed_at must include a timezone.")


@dataclass(frozen=True, slots=True)
class FindingTechnicalEffectProjection:
    finding_id: str
    status: FindingTechnicalEffectStatus
    effects: tuple[FindingTechnicalEffect, ...]
    missing_requirements: tuple[str, ...]
    completeness: ExplanationCompleteness

    def __post_init__(self) -> None:
        if type(self.finding_id) is not str or not self.finding_id.strip():
            raise ValueError("Technical effect projection requires a finding ID.")
        if not isinstance(self.status, FindingTechnicalEffectStatus):
            raise ValueError("Technical effect projection status is invalid.")
        if not isinstance(self.effects, tuple) or not all(isinstance(item, FindingTechnicalEffect) for item in self.effects):
            raise ValueError("Technical effects are invalid.")
        if not isinstance(self.missing_requirements, tuple) or not all(type(item) is str and item.strip() for item in self.missing_requirements):
            raise ValueError("Technical effect missing requirements are invalid.")
        if not isinstance(self.completeness, ExplanationCompleteness):
            raise ValueError("Technical effect completeness is invalid.")
        expected_reference = f"finding-technical-effect:{self.status.value.lower()}:{self.finding_id}"
        if self.completeness.provenance.source_type != "finding_technical_effect" or self.completeness.provenance.source_reference != expected_reference:
            raise ValueError("Technical effect result provenance is invalid.")
        if any(item.finding_id != self.finding_id for item in self.effects):
            raise ValueError("Technical effects identify another finding.")
        identifiers = tuple(item.cve_identifier for item in self.effects)
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Technical effects must retain unique CVE identities.")
        if self.status is FindingTechnicalEffectStatus.AVAILABLE:
            if not self.effects or self.missing_requirements or self.completeness.status is not CompletenessStatus.AVAILABLE:
                raise ValueError("Available technical effect projection is inconsistent.")
        elif self.status is FindingTechnicalEffectStatus.UNAVAILABLE:
            if self.effects or not self.missing_requirements or self.completeness.status is CompletenessStatus.AVAILABLE:
                raise ValueError("Unavailable technical effect projection is inconsistent.")
        else:
            raise ValueError("Technical effect projection status is invalid.")


class FindingTechnicalEffectService:
    _LEVELS = {"N": TechnicalEffectLevel.NONE, "L": TechnicalEffectLevel.LOW, "H": TechnicalEffectLevel.HIGH}

    def project(self, enrichment: FindingThreatIntelligenceEnrichment) -> FindingTechnicalEffectProjection:
        effects: list[FindingTechnicalEffect] = []
        failures: list[str] = []
        for relationship in enrichment.relationships:
            vulnerability = relationship.vulnerability
            if relationship.applicability is not FindingIntelligenceApplicability.APPLICABLE or vulnerability is None:
                failures.append("applicable_technical_effect")
                continue
            cvss = vulnerability.cvss
            if cvss.completeness.status is not CompletenessStatus.AVAILABLE or cvss.value is None:
                failures.append(f"technical_effect:{vulnerability.cve_identifier.value}")
                continue
            parsed = self._parse_vector(cvss.value.version, cvss.value.vector)
            if parsed is None:
                failures.append(f"supported_cvss_v3_effect:{vulnerability.cve_identifier.value}")
                continue
            effects.append(FindingTechnicalEffect(
                finding_id=enrichment.finding_id,
                cve_identifier=vulnerability.cve_identifier.value,
                cvss_vector=cvss.value.vector,
                confidentiality=parsed[0], integrity=parsed[1], availability=parsed[2],
                source_reference=cvss.provenance.source_reference,
                observed_at=cvss.observed_at,
            ))
        if failures or not effects:
            missing = tuple(dict.fromkeys(failures or ("applicable_technical_effect",)))
            return self._result(enrichment.finding_id, FindingTechnicalEffectStatus.UNAVAILABLE, (), missing, CompletenessStatus.NO_DATA)
        return self._result(enrichment.finding_id, FindingTechnicalEffectStatus.AVAILABLE, tuple(effects), (), CompletenessStatus.AVAILABLE)

    @classmethod
    def _parse_vector(cls, version: str, vector: str) -> tuple[TechnicalEffectLevel, TechnicalEffectLevel, TechnicalEffectLevel] | None:
        if version not in {"3.0", "3.1"} or not vector.startswith(("CVSS:3.0/", "CVSS:3.1/")):
            return None
        metrics: dict[str, str] = {}
        for item in vector.split("/")[1:]:
            parts = item.split(":")
            if len(parts) != 2 or parts[0] in metrics:
                return None
            metrics[parts[0]] = parts[1]
        if any(metrics.get(name) not in cls._LEVELS for name in ("C", "I", "A")):
            return None
        return (cls._LEVELS[metrics["C"]], cls._LEVELS[metrics["I"]], cls._LEVELS[metrics["A"]])

    @staticmethod
    def _result(finding_id: str, status: FindingTechnicalEffectStatus, effects: tuple[FindingTechnicalEffect, ...], missing: tuple[str, ...], completeness_status: CompletenessStatus) -> FindingTechnicalEffectProjection:
        return FindingTechnicalEffectProjection(
            finding_id, status, effects, missing,
            ExplanationCompleteness(completeness_status, ExplanationProvenance("finding_technical_effect", f"finding-technical-effect:{status.value.lower()}:{finding_id}")),
        )
