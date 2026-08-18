from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Protocol

from core.incident_response import (
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentLifecycleStatus,
    IncidentParticipant,
    IncidentParticipantRole,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentReferenceType,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


SECURITY_INCIDENT_CONTEXT_STORE_VERSION = "1.0"
_ROOT_KEYS = {"contractVersion", "incidents"}


class IncidentContextConfigurationError(ValueError):
    """Raised when the configured incident context file is unavailable."""


class IncidentContextDataError(ValueError):
    """Raised when persisted incident context is invalid."""


class IncidentContextRepository(Protocol):
    def get(self, incident_id: str) -> SecurityIncidentContext | None:
        ...

    def save(self, context: SecurityIncidentContext) -> None:
        ...


class FileIncidentContextRepository:
    """Strict JSON adapter for the canonical SecurityIncidentContext contract."""

    def __init__(self, path: str | None) -> None:
        self._path = path

    def get(self, incident_id: str) -> SecurityIncidentContext | None:
        normalized_id = self._required_string(incident_id, "Incident ID")
        document = self._read_document()
        for record in document["incidents"]:
            context = self._parse_context(record)
            if context.incident_id == normalized_id:
                return context
        return None

    def save(self, context: SecurityIncidentContext) -> None:
        if not isinstance(context, SecurityIncidentContext):
            raise ValueError("Incident repository requires a canonical context.")
        if context.contract_version != SECURITY_INCIDENT_CONTEXT_STORE_VERSION:
            raise IncidentContextDataError(
                "Incident context contract version is unsupported."
            )

        document = self._read_document(allow_missing=True)
        records = list(document["incidents"])
        serialized = _serialize_context(context)
        replaced = False
        for index, record in enumerate(records):
            if record.get("incidentId") == context.incident_id:
                records[index] = serialized
                replaced = True
                break
        if not replaced:
            records.append(serialized)

        self._write_document(
            {
                "contractVersion": SECURITY_INCIDENT_CONTEXT_STORE_VERSION,
                "incidents": records,
            }
        )

    def _read_document(self, *, allow_missing: bool = False) -> dict[str, object]:
        path = self._configured_path()
        if not path.exists():
            if allow_missing:
                return {
                    "contractVersion": SECURITY_INCIDENT_CONTEXT_STORE_VERSION,
                    "incidents": [],
                }
            raise IncidentContextConfigurationError(
                "INCIDENT_CONTEXT_PATH cannot be read."
            )
        try:
            source_text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise IncidentContextConfigurationError(
                "INCIDENT_CONTEXT_PATH cannot be read."
            ) from error
        try:
            document = json.loads(source_text)
        except json.JSONDecodeError as error:
            raise IncidentContextDataError(
                "Incident context source is not valid JSON."
            ) from error
        return self._validate_document(document)

    def _write_document(self, document: dict[str, object]) -> None:
        path = self._configured_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(document, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        except OSError as error:
            raise IncidentContextConfigurationError(
                "INCIDENT_CONTEXT_PATH cannot be written."
            ) from error

    def _configured_path(self) -> Path:
        if self._path is None or not self._path.strip():
            raise IncidentContextConfigurationError(
                "INCIDENT_CONTEXT_PATH is not configured."
            )
        return Path(self._path)

    @classmethod
    def _validate_document(cls, document: object) -> dict[str, object]:
        if not isinstance(document, dict) or set(document) != _ROOT_KEYS:
            raise IncidentContextDataError(
                "Incident context source has an invalid schema."
            )
        if document["contractVersion"] != SECURITY_INCIDENT_CONTEXT_STORE_VERSION:
            raise IncidentContextDataError(
                "Incident context source contract version is unsupported."
            )
        if not isinstance(document["incidents"], list):
            raise IncidentContextDataError("Incident contexts must be a list.")
        return document

    @classmethod
    def _parse_context(cls, record: object) -> SecurityIncidentContext:
        if not isinstance(record, dict):
            raise IncidentContextDataError("Incident context record must be an object.")
        required_keys = {
            "incidentId",
            "lifecycleStatus",
            "source",
            "sourceReference",
            "title",
            "createdAt",
            "updatedAt",
            "owner",
            "participants",
            "description",
            "relationships",
            "contractVersion",
        }
        if set(record) != required_keys:
            raise IncidentContextDataError("Incident context record has an invalid schema.")
        try:
            return SecurityIncidentContext(
                incident_id=cls._required_string(record["incidentId"], "incidentId"),
                lifecycle_status=IncidentLifecycleStatus(
                    cls._required_string(record["lifecycleStatus"], "lifecycleStatus")
                ),
                source=cls._required_string(record["source"], "source"),
                source_reference=cls._required_string(
                    record["sourceReference"], "sourceReference"
                ),
                title=cls._required_string(record["title"], "title"),
                created_at=cls._timestamp(record["createdAt"], "createdAt"),
                updated_at=cls._timestamp(record["updatedAt"], "updatedAt"),
                owner=(
                    cls._parse_principal(record["owner"])
                    if record["owner"] is not None
                    else None
                ),
                participants=tuple(
                    cls._parse_participant(item) for item in cls._list(record["participants"], "participants")
                ),
                description=(
                    cls._required_string(record["description"], "description")
                    if record["description"] is not None
                    else None
                ),
                relationships=tuple(
                    cls._parse_relationship(item)
                    for item in cls._list(record["relationships"], "relationships")
                ),
                contract_version=cls._required_string(
                    record["contractVersion"], "contractVersion"
                ),
            )
        except (TypeError, ValueError) as error:
            if isinstance(error, IncidentContextDataError):
                raise
            raise IncidentContextDataError(
                "Incident context record contains an invalid value."
            ) from error

    @classmethod
    def _parse_principal(cls, value: object) -> IncidentPrincipalReference:
        record = cls._record(value, {"principalType", "principalId"}, "principal")
        return IncidentPrincipalReference(
            principal_type=IncidentPrincipalType(
                cls._required_string(record["principalType"], "principalType")
            ),
            principal_id=cls._required_string(record["principalId"], "principalId"),
        )

    @classmethod
    def _parse_participant(cls, value: object) -> IncidentParticipant:
        record = cls._record(value, {"principal", "role"}, "participant")
        return IncidentParticipant(
            principal=cls._parse_principal(record["principal"]),
            role=IncidentParticipantRole(
                cls._required_string(record["role"], "role")
            ),
        )

    @classmethod
    def _parse_relationship(cls, value: object) -> IncidentRelationship:
        record = cls._record(
            value,
            {"relationshipId", "role", "target"},
            "relationship",
        )
        role = IncidentRelationshipRole(
            cls._required_string(record["role"], "role")
        )
        return IncidentRelationship(
            relationship_id=cls._required_string(
                record["relationshipId"], "relationshipId"
            ),
            role=role,
            target=cls._parse_target(role, record["target"]),
        )

    @classmethod
    def _parse_target(
        cls,
        role: IncidentRelationshipRole,
        value: object,
    ):
        if role is IncidentRelationshipRole.INVESTIGATION_CANDIDATE:
            record = cls._record(value, {"findingId", "source"}, "finding target")
            return FindingReference(
                finding_id=cls._required_string(record["findingId"], "findingId"),
                source=cls._required_string(record["source"], "source"),
            )
        if role is IncidentRelationshipRole.AFFECTED_ASSET:
            record = cls._record(value, {"canonicalAssetId"}, "asset target")
            return CanonicalAssetReference(
                cls._required_string(record["canonicalAssetId"], "canonicalAssetId")
            )
        if role is IncidentRelationshipRole.THREAT_CONTEXT:
            record = cls._record(
                value,
                {"referenceId", "contractVersion"},
                "threat intelligence target",
            )
            return ThreatIntelligenceReference(
                reference_id=cls._required_string(record["referenceId"], "referenceId"),
                contract_version=cls._required_string(
                    record["contractVersion"], "contractVersion"
                ),
            )
        if role is IncidentRelationshipRole.SUPPORTING_EVIDENCE:
            record = cls._record(
                value,
                {"evidenceId", "contractVersion"},
                "evidence target",
            )
            return EvidenceReference(
                evidence_id=cls._required_string(record["evidenceId"], "evidenceId"),
                contract_version=cls._required_string(
                    record["contractVersion"], "contractVersion"
                ),
            )
        record = cls._record(
            value,
            {"decisionId", "versionId", "evidenceSnapshotId"},
            "decision target",
        )
        return DecisionVersionReference(
            decision_id=cls._required_string(record["decisionId"], "decisionId"),
            version_id=cls._required_string(record["versionId"], "versionId"),
            evidence_snapshot_id=(
                cls._required_string(record["evidenceSnapshotId"], "evidenceSnapshotId")
                if record["evidenceSnapshotId"] is not None
                else None
            ),
        )

    @staticmethod
    def _record(
        value: object,
        keys: set[str],
        label: str,
    ) -> dict[str, object]:
        if not isinstance(value, dict) or set(value) != keys:
            raise IncidentContextDataError(f"{label} has an invalid schema.")
        return value

    @staticmethod
    def _list(value: object, label: str) -> list[object]:
        if not isinstance(value, list):
            raise IncidentContextDataError(f"{label} must be a list.")
        return value

    @staticmethod
    def _required_string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise IncidentContextDataError(f"{label} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _timestamp(cls, value: object, label: str) -> datetime:
        raw = cls._required_string(value, label)
        try:
            parsed = datetime.fromisoformat(raw)
        except ValueError as error:
            raise IncidentContextDataError(f"{label} must be ISO-8601.") from error
        if parsed.utcoffset() is None:
            raise IncidentContextDataError(f"{label} must be timezone-aware.")
        return parsed


class IncidentContextCreationService:
    """Controlled internal creation boundary; no HTTP write surface."""

    def __init__(self, repository: IncidentContextRepository) -> None:
        self._repository = repository

    def create(self, context: SecurityIncidentContext) -> SecurityIncidentContext:
        if not isinstance(context, SecurityIncidentContext):
            raise ValueError("Incident creation requires a canonical context.")
        self._repository.save(context)
        return context


class IncidentOwnerAssignmentService:
    """Assign an incident owner through the canonical repository boundary."""

    def __init__(self, repository: IncidentContextRepository) -> None:
        self._repository = repository

    def assign(
        self,
        incident_id: str,
        owner: IncidentPrincipalReference,
    ) -> SecurityIncidentContext:
        if not isinstance(owner, IncidentPrincipalReference):
            raise ValueError("Incident owner must be a canonical principal reference.")

        context = self._repository.get(incident_id)
        if context is None:
            raise LookupError("Incident context was not found.")

        updated_context = replace(context, owner=owner)
        self._repository.save(updated_context)
        return updated_context


def _serialize_context(context: SecurityIncidentContext) -> dict[str, object]:
    return {
        "incidentId": context.incident_id,
        "lifecycleStatus": context.lifecycle_status.value,
        "source": context.source,
        "sourceReference": context.source_reference,
        "title": context.title,
        "createdAt": context.created_at.isoformat(),
        "updatedAt": context.updated_at.isoformat(),
        "owner": _serialize_principal(context.owner),
        "participants": [
            {
                "principal": _serialize_principal(item.principal),
                "role": item.role.value,
            }
            for item in context.participants
        ],
        "description": context.description,
        "relationships": [
            {
                "relationshipId": relationship.relationship_id,
                "role": relationship.role.value,
                "target": _serialize_target(relationship.target),
            }
            for relationship in context.relationships
        ],
        "contractVersion": context.contract_version,
    }


def _serialize_principal(
    principal: IncidentPrincipalReference | None,
) -> dict[str, str] | None:
    if principal is None:
        return None
    return {
        "principalType": principal.principal_type.value,
        "principalId": principal.principal_id,
    }


def _serialize_target(reference: object) -> dict[str, object]:
    if isinstance(reference, FindingReference):
        return {"findingId": reference.finding_id, "source": reference.source}
    if isinstance(reference, CanonicalAssetReference):
        return {"canonicalAssetId": reference.canonical_asset_id}
    if isinstance(reference, ThreatIntelligenceReference):
        return {
            "referenceId": reference.reference_id,
            "contractVersion": reference.contract_version,
        }
    if isinstance(reference, EvidenceReference):
        return {
            "evidenceId": reference.evidence_id,
            "contractVersion": reference.contract_version,
        }
    if isinstance(reference, DecisionVersionReference):
        return {
            "decisionId": reference.decision_id,
            "versionId": reference.version_id,
            "evidenceSnapshotId": reference.evidence_snapshot_id,
        }
    raise ValueError("Unsupported incident reference.")
