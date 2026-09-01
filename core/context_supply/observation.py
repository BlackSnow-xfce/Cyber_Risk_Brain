from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Mapping


class ContextType(str, Enum):
    EXPOSURE = "EXPOSURE"
    DETECTION_COVERAGE = "DETECTION_COVERAGE"
    MITRE_MAPPING = "MITRE_MAPPING"
    REVOCATION = "REVOCATION"


class ObservationStatus(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    CONFLICTED = "CONFLICTED"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
    UNKNOWN = "UNKNOWN"


def require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware.")


@dataclass(frozen=True, slots=True)
class ContextSubject:
    asset_id: str
    finding_id: str

    def __post_init__(self) -> None:
        if not self.asset_id.strip() or not self.finding_id.strip():
            raise ValueError("Context subject requires asset and finding IDs.")


@dataclass(frozen=True, slots=True)
class ContextScope:
    service: str
    path: str
    technique_id: str | None = None

    def __post_init__(self) -> None:
        if not self.service.strip() or not self.path.strip():
            raise ValueError("Context scope requires exact service and path.")

    @property
    def identity(self) -> str:
        return "|".join((self.service, self.path, self.technique_id or ""))


@dataclass(frozen=True, slots=True)
class ObservationProvenance:
    source_reference: str
    evidence_references: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.source_reference.strip() or not self.evidence_references:
            raise ValueError("Observation provenance requires source and evidence.")
        if any(not item.strip() for item in self.evidence_references):
            raise ValueError("Evidence references cannot be empty.")


@dataclass(frozen=True, slots=True)
class ContextObservation:
    observation_id: str
    organization_id: str
    context_type: ContextType
    subject: ContextSubject
    scope: ContextScope
    source_id: str
    authority_reference: str
    provenance: ObservationProvenance
    observed_at: datetime
    ingested_at: datetime
    valid_until: datetime
    schema_version: str
    payload: object
    digest: str = field(default="")
    supersedes_observation_id: str | None = None
    revokes_observation_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("observation_id", "organization_id", "source_id", "authority_reference", "schema_version"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} is required.")
        for name in ("observed_at", "ingested_at", "valid_until"):
            require_aware(getattr(self, name), name)
        if self.observed_at > self.ingested_at or self.valid_until <= self.observed_at:
            raise ValueError("Observation timestamps are invalid.")
        if self.schema_version != "1.0":
            raise ValueError("Unsupported observation schema version.")
        if self.supersedes_observation_id == self.observation_id or self.revokes_observation_id == self.observation_id:
            raise ValueError("An observation cannot supersede or revoke itself.")
        expected_id = self.deterministic_id()
        if self.observation_id != expected_id:
            raise ValueError("Observation identity is not deterministic.")
        expected_digest = self.calculate_digest()
        if self.digest:
            if self.digest != expected_digest:
                raise ValueError("Observation digest mismatch.")
        else:
            object.__setattr__(self, "digest", expected_digest)

    def _identity_document(self) -> Mapping[str, object]:
        return {
            "organization_id": self.organization_id,
            "context_type": self.context_type.value,
            "subject": {"asset_id": self.subject.asset_id, "finding_id": self.subject.finding_id},
            "scope": {"service": self.scope.service, "path": self.scope.path, "technique_id": self.scope.technique_id},
            "source_id": self.source_id,
            "observed_at": self.observed_at.isoformat(),
        }

    def deterministic_id(self) -> str:
        value = json.dumps(self._identity_document(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(value.encode()).hexdigest()

    def calculate_digest(self) -> str:
        document = dict(self._identity_document())
        document.update({
            "authority_reference": self.authority_reference,
            "provenance": {"source_reference": self.provenance.source_reference, "evidence_references": self.provenance.evidence_references},
            "ingested_at": self.ingested_at.isoformat(), "valid_until": self.valid_until.isoformat(),
            "schema_version": self.schema_version, "payload": self.payload,
            "supersedes": self.supersedes_observation_id, "revokes": self.revokes_observation_id,
        })
        value = json.dumps(document, sort_keys=True, separators=(",", ":"), default=lambda item: item.value if isinstance(item, Enum) else asdict(item) if is_dataclass(item) else str(item))
        return hashlib.sha256(value.encode()).hexdigest()

    @classmethod
    def create(cls, *, organization_id: str, context_type: ContextType, subject: ContextSubject, scope: ContextScope, source_id: str, authority_reference: str, provenance: ObservationProvenance, observed_at: datetime, ingested_at: datetime, valid_until: datetime, payload: object, schema_version: str = "1.0", supersedes_observation_id: str | None = None, revokes_observation_id: str | None = None) -> "ContextObservation":
        identity = {"organization_id": organization_id, "context_type": context_type.value, "subject": {"asset_id": subject.asset_id, "finding_id": subject.finding_id}, "scope": {"service": scope.service, "path": scope.path, "technique_id": scope.technique_id}, "source_id": source_id, "observed_at": observed_at.isoformat()}
        observation_id = hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return cls(observation_id, organization_id, context_type, subject, scope, source_id, authority_reference, provenance, observed_at, ingested_at, valid_until, schema_version, payload, "", supersedes_observation_id, revokes_observation_id)

    def is_current(self, at: datetime | None = None) -> bool:
        instant = at or datetime.now(timezone.utc)
        require_aware(instant, "at")
        return self.observed_at <= instant < self.valid_until
