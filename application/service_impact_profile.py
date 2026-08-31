from __future__ import annotations

import json
from pathlib import Path

from core.enterprise_context import BusinessImportance, ServiceImpactProfile


class ServiceImpactProfileDataError(ValueError):
    """Configured Service Impact Profile authority is invalid."""


class ServiceImpactProfileQueryService:
    _ROOT_KEYS = {"serviceImpactProfiles"}
    _RECORD_KEYS = {
        "canonicalAssetId", "businessService", "confidentialityImportance",
        "integrityImportance", "availabilityImportance", "sourceReference",
    }

    def __init__(self, profile_path: str | None) -> None:
        self._profile_path = profile_path

    def resolve(self, canonical_asset_id: str) -> ServiceImpactProfile | None:
        if type(canonical_asset_id) is not str or not canonical_asset_id or canonical_asset_id != canonical_asset_id.strip():
            raise ValueError("Canonical asset ID is invalid.")
        if self._profile_path is None or not self._profile_path.strip():
            return None
        profiles = self._load()
        matches = [item for item in profiles if item.canonical_asset_id == canonical_asset_id]
        if len(matches) > 1:
            raise ServiceImpactProfileDataError("Service impact profile authority is ambiguous.")
        return matches[0] if matches else None

    def _load(self) -> tuple[ServiceImpactProfile, ...]:
        try:
            document = json.loads(Path(self._profile_path or "").read_text(encoding="utf-8"))
        except OSError as error:
            raise ServiceImpactProfileDataError("Service impact profile authority cannot be read.") from error
        except json.JSONDecodeError as error:
            raise ServiceImpactProfileDataError("Service impact profile authority is not valid JSON.") from error
        if not isinstance(document, dict) or set(document) != self._ROOT_KEYS:
            raise ServiceImpactProfileDataError("Service impact profile authority has an invalid root schema.")
        records = document["serviceImpactProfiles"]
        if not isinstance(records, list):
            raise ServiceImpactProfileDataError("Service impact profiles must be a list.")
        profiles = tuple(self._parse_record(record) for record in records)
        identifiers = [item.canonical_asset_id for item in profiles]
        if len(identifiers) != len(set(identifiers)):
            raise ServiceImpactProfileDataError("Service impact profile authority contains duplicate canonical assets.")
        return profiles

    @classmethod
    def _parse_record(cls, record: object) -> ServiceImpactProfile:
        if not isinstance(record, dict) or set(record) != cls._RECORD_KEYS:
            raise ServiceImpactProfileDataError("Service impact profile record has an invalid schema.")
        try:
            return ServiceImpactProfile(
                canonical_asset_id=cls._string(record, "canonicalAssetId"),
                business_service=cls._string(record, "businessService"),
                confidentiality_importance=BusinessImportance(cls._string(record, "confidentialityImportance")),
                integrity_importance=BusinessImportance(cls._string(record, "integrityImportance")),
                availability_importance=BusinessImportance(cls._string(record, "availabilityImportance")),
                source_reference=cls._string(record, "sourceReference"),
            )
        except (TypeError, ValueError) as error:
            raise ServiceImpactProfileDataError("Service impact profile record contains an invalid value.") from error

    @staticmethod
    def _string(record: dict[object, object], key: str) -> str:
        value = record[key]
        if type(value) is not str or not value or value != value.strip():
            raise ServiceImpactProfileDataError(f"Service impact profile {key} is invalid.")
        return value
