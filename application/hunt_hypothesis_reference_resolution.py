from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.asset_context import (
    AssetContextConfigurationError,
    AssetContextDataError,
    AssetContextQueryService,
)
from application.findings_query import FindingsConfigurationError, FindingsQueryService
from application.hunt_hypotheses import HuntHypothesisQueryService
from application.threat_intelligence import (
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceDataError,
    ThreatIntelligenceInvalidResponseError,
    ThreatIntelligenceNotFoundError,
    ThreatIntelligenceQueryService,
    ThreatIntelligenceSourceUnavailableError,
    ThreatIntelligenceTimeoutError,
)
from core.threat_hunting import HuntHypothesisReference, HuntHypothesisReferenceType


class HuntHypothesisReferenceResolutionStatus(StrEnum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    SOURCE_UNAVAILABLE = "source_unavailable"
    UNSUPPORTED = "unsupported"


class HuntHypothesisNotFoundError(LookupError):
    """Raised when the exact persisted hypothesis does not exist."""


class HuntHypothesisReferenceIntegrityError(ValueError):
    """Raised when an authoritative source cannot be trusted."""


@dataclass(frozen=True, slots=True)
class HuntHypothesisReferenceResolution:
    reference_type: HuntHypothesisReferenceType
    reference_id: str
    resolution_status: HuntHypothesisReferenceResolutionStatus
    authoritative_source: str | None = None
    resolved_identity: str | None = None
    source_reference: str | None = None


@dataclass(frozen=True, slots=True)
class HuntHypothesisReferenceResolutionResult:
    hypothesis_id: str
    references: tuple[HuntHypothesisReferenceResolution, ...]


class HuntHypothesisReferenceResolutionService:
    """Resolve approved pointers without changing the canonical hypothesis."""

    def __init__(
        self,
        hypotheses: HuntHypothesisQueryService,
        findings: FindingsQueryService,
        assets: AssetContextQueryService,
        threat_intelligence: ThreatIntelligenceQueryService,
    ) -> None:
        self._hypotheses = hypotheses
        self._findings = findings
        self._assets = assets
        self._threat_intelligence = threat_intelligence

    def resolve(self, hypothesis_id: str) -> HuntHypothesisReferenceResolutionResult:
        normalized_id = hypothesis_id.strip()
        if not normalized_id:
            raise HuntHypothesisNotFoundError("Hunt Hypothesis was not found.")
        matches = [
            hypothesis
            for hypothesis in self._hypotheses.list()
            if hypothesis.hypothesis_id == normalized_id
        ]
        if not matches:
            raise HuntHypothesisNotFoundError("Hunt Hypothesis was not found.")
        if len(matches) != 1:
            raise HuntHypothesisReferenceIntegrityError(
                "Hunt Hypothesis identity is ambiguous."
            )

        hypothesis = matches[0]
        references = hypothesis.target_references + hypothesis.threat_references
        return HuntHypothesisReferenceResolutionResult(
            hypothesis_id=hypothesis.hypothesis_id,
            references=tuple(self._resolve_reference(item) for item in references),
        )

    def _resolve_reference(
        self, reference: HuntHypothesisReference
    ) -> HuntHypothesisReferenceResolution:
        if reference.reference_type is HuntHypothesisReferenceType.FINDING:
            return self._resolve_finding(reference)
        if reference.reference_type is HuntHypothesisReferenceType.ASSET:
            return self._resolve_asset(reference)
        if reference.reference_type is HuntHypothesisReferenceType.CVE:
            return self._resolve_cve(reference)
        return HuntHypothesisReferenceResolution(
            reference_type=reference.reference_type,
            reference_id=reference.reference_id,
            resolution_status=HuntHypothesisReferenceResolutionStatus.UNSUPPORTED,
        )

    def _resolve_finding(
        self, reference: HuntHypothesisReference
    ) -> HuntHypothesisReferenceResolution:
        try:
            findings = self._findings.get_findings()
        except (FindingsConfigurationError, OSError):
            return self._unavailable(reference, "findings")
        except ValueError as error:
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Finding source contains invalid data."
            ) from error

        finding_ids = [getattr(finding, "id", None) for finding in findings]
        if any(not isinstance(item, str) or not item.strip() for item in finding_ids):
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Finding source contains invalid data."
            )
        if len(set(finding_ids)) != len(finding_ids):
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Finding source contains a duplicate identity."
            )
        matches = [
            finding
            for finding in findings
            if finding.id == reference.reference_id
        ]
        if not matches:
            return self._not_found(reference, "findings")
        finding = matches[0]
        source = getattr(finding, "source", None)
        if not isinstance(source, str) or not source.strip():
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Finding source contains invalid data."
            )
        return self._resolved(
            reference,
            authoritative_source="findings",
            source_reference=source.strip(),
        )

    def _resolve_asset(
        self, reference: HuntHypothesisReference
    ) -> HuntHypothesisReferenceResolution:
        try:
            asset = self._assets.resolve_canonical_asset(reference.reference_id)
        except AssetContextConfigurationError:
            return self._unavailable(reference, "asset_context")
        except (AssetContextDataError, ValueError) as error:
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Asset source contains invalid data."
            ) from error
        if asset is None:
            return self._not_found(reference, "asset_context")
        canonical_id = getattr(asset, "canonical_asset_id", None)
        source_reference = getattr(asset, "source_reference", None)
        if canonical_id != reference.reference_id or not isinstance(
            source_reference, str
        ) or not source_reference.strip():
            raise HuntHypothesisReferenceIntegrityError(
                "Configured Asset source returned an inconsistent identity."
            )
        return self._resolved(
            reference,
            authoritative_source="asset_context",
            source_reference=source_reference.strip(),
        )

    def _resolve_cve(
        self, reference: HuntHypothesisReference
    ) -> HuntHypothesisReferenceResolution:
        try:
            intelligence = self._threat_intelligence.get_by_cve(
                reference.reference_id
            )
        except ThreatIntelligenceNotFoundError:
            return self._not_found(reference, "threat_intelligence")
        except (
            ThreatIntelligenceConfigurationError,
            ThreatIntelligenceSourceUnavailableError,
            ThreatIntelligenceTimeoutError,
        ):
            return self._unavailable(reference, "threat_intelligence")
        except (
            ThreatIntelligenceDataError,
            ThreatIntelligenceInvalidResponseError,
            ValueError,
        ) as error:
            raise HuntHypothesisReferenceIntegrityError(
                "Threat Intelligence source contains invalid data."
            ) from error
        cve_identifier = getattr(intelligence, "cve_identifier", None)
        resolved_value = getattr(cve_identifier, "value", None)
        contract_version = getattr(intelligence, "contract_version", None)
        if resolved_value != reference.reference_id.upper() or not isinstance(
            contract_version, str
        ) or not contract_version.strip():
            raise HuntHypothesisReferenceIntegrityError(
                "Threat Intelligence source returned an inconsistent identity."
            )
        return self._resolved(
            reference,
            authoritative_source="threat_intelligence",
            source_reference=f"contract:{contract_version.strip()}",
            resolved_identity=resolved_value,
        )

    @staticmethod
    def _resolved(
        reference: HuntHypothesisReference,
        *,
        authoritative_source: str,
        source_reference: str,
        resolved_identity: str | None = None,
    ) -> HuntHypothesisReferenceResolution:
        return HuntHypothesisReferenceResolution(
            reference_type=reference.reference_type,
            reference_id=reference.reference_id,
            resolution_status=HuntHypothesisReferenceResolutionStatus.RESOLVED,
            authoritative_source=authoritative_source,
            resolved_identity=resolved_identity or reference.reference_id,
            source_reference=source_reference,
        )

    @staticmethod
    def _not_found(
        reference: HuntHypothesisReference, authoritative_source: str
    ) -> HuntHypothesisReferenceResolution:
        return HuntHypothesisReferenceResolution(
            reference_type=reference.reference_type,
            reference_id=reference.reference_id,
            resolution_status=HuntHypothesisReferenceResolutionStatus.NOT_FOUND,
            authoritative_source=authoritative_source,
        )

    @staticmethod
    def _unavailable(
        reference: HuntHypothesisReference, authoritative_source: str
    ) -> HuntHypothesisReferenceResolution:
        return HuntHypothesisReferenceResolution(
            reference_type=reference.reference_type,
            reference_id=reference.reference_id,
            resolution_status=(
                HuntHypothesisReferenceResolutionStatus.SOURCE_UNAVAILABLE
            ),
            authoritative_source=authoritative_source,
        )
