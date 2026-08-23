from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


HUNT_HYPOTHESIS_CONTRACT_VERSION = "1.0"


class HuntHypothesisStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    CLOSED = "closed"


class HuntHypothesisReferenceType(StrEnum):
    ASSET = "asset"
    SERVICE = "service"
    FINDING = "finding"
    CVE = "cve"
    THREAT_INTELLIGENCE = "threat_intelligence"
    TECHNIQUE = "technique"
    TACTIC = "tactic"


_TARGET_REFERENCE_TYPES = frozenset({
    HuntHypothesisReferenceType.ASSET,
    HuntHypothesisReferenceType.SERVICE,
    HuntHypothesisReferenceType.FINDING,
})
_THREAT_REFERENCE_TYPES = frozenset({
    HuntHypothesisReferenceType.CVE,
    HuntHypothesisReferenceType.THREAT_INTELLIGENCE,
    HuntHypothesisReferenceType.TECHNIQUE,
    HuntHypothesisReferenceType.TACTIC,
})


@dataclass(frozen=True, slots=True)
class HuntHypothesisReference:
    """Typed pointer to an existing security object or threat identifier."""

    reference_type: HuntHypothesisReferenceType
    reference_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.reference_type, HuntHypothesisReferenceType):
            raise ValueError("reference_type must be canonical.")
        if not isinstance(self.reference_id, str) or not self.reference_id.strip():
            raise ValueError("reference_id must not be empty.")
        object.__setattr__(self, "reference_id", self.reference_id.strip())

    def to_dict(self) -> dict[str, str]:
        return {
            "reference_type": self.reference_type.value,
            "reference_id": self.reference_id,
        }


@dataclass(frozen=True, slots=True)
class HuntHypothesis:
    """An explicit, testable assumption that is not a confirmed finding."""

    hypothesis_id: str
    title: str
    statement: str
    status: HuntHypothesisStatus
    created_at: datetime
    created_by: str
    target_references: tuple[HuntHypothesisReference, ...]
    threat_references: tuple[HuntHypothesisReference, ...]
    rationale: str
    contract_version: str = HUNT_HYPOTHESIS_CONTRACT_VERSION

    def __post_init__(self) -> None:
        for field_name, value in (
            ("hypothesis_id", self.hypothesis_id),
            ("title", self.title),
            ("statement", self.statement),
            ("created_by", self.created_by),
            ("rationale", self.rationale),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty.")
            object.__setattr__(self, field_name, value.strip())

        if not isinstance(self.status, HuntHypothesisStatus):
            raise ValueError("status must be a HuntHypothesisStatus.")
        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be a datetime.")
        if self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware.")
        if self.contract_version != HUNT_HYPOTHESIS_CONTRACT_VERSION:
            raise ValueError(
                "contract_version must be "
                f"{HUNT_HYPOTHESIS_CONTRACT_VERSION}."
            )

        self._validate_references(self.target_references, "target_references", _TARGET_REFERENCE_TYPES)
        self._validate_references(self.threat_references, "threat_references", _THREAT_REFERENCE_TYPES)

    @staticmethod
    def _validate_references(
        references: tuple[HuntHypothesisReference, ...],
        field_name: str,
        allowed_types: frozenset[HuntHypothesisReferenceType],
    ) -> None:
        if not isinstance(references, tuple):
            raise ValueError(f"{field_name} must be a tuple.")
        if any(not isinstance(reference, HuntHypothesisReference) for reference in references):
            raise ValueError(f"{field_name} contains an invalid reference.")
        if any(reference.reference_type not in allowed_types for reference in references):
            raise ValueError(f"{field_name} contains a reference of the wrong category.")
        if len(set(references)) != len(references):
            raise ValueError(f"{field_name} must not contain duplicate references.")

    def to_dict(self) -> dict[str, object]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "statement": self.statement,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "target_references": [
                reference.to_dict() for reference in self.target_references
            ],
            "threat_references": [
                reference.to_dict() for reference in self.threat_references
            ],
            "rationale": self.rationale,
            "contract_version": self.contract_version,
        }
