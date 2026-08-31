from __future__ import annotations

import json
from pathlib import Path

from core.enterprise_context import (
    AssetBusinessContext,
    BusinessEnvironment,
    ServiceCriticality,
)


class AssetBusinessContextDataError(ValueError):
    """Raised when the configured business-context authority is invalid."""


class AssetBusinessContextQueryService:
    """Resolve immutable organizational facts from one strict JSON authority."""

    _ROOT_KEYS = {"assetBusinessContexts"}
    _RECORD_KEYS = {
        "canonicalAssetId",
        "businessService",
        "environment",
        "serviceCriticality",
        "sourceReference",
    }

    def __init__(self, context_path: str | None) -> None:
        self._context_path = context_path

    def resolve(self, canonical_asset_id: str) -> AssetBusinessContext | None:
        normalized_id = canonical_asset_id.strip()
        if not normalized_id:
            raise ValueError("Canonical asset ID must not be empty.")
        if self._context_path is None or not self._context_path.strip():
            return None
        contexts = self._load_contexts()
        matches = [item for item in contexts if item.canonical_asset_id == normalized_id]
        if len(matches) > 1:
            raise AssetBusinessContextDataError(
                "Business context source contains an ambiguous canonical asset."
            )
        return matches[0] if matches else None

    def _load_contexts(self) -> tuple[AssetBusinessContext, ...]:
        try:
            document = json.loads(
                Path(self._context_path or "").read_text(encoding="utf-8")
            )
        except OSError as error:
            raise AssetBusinessContextDataError(
                "Business context source cannot be read."
            ) from error
        except json.JSONDecodeError as error:
            raise AssetBusinessContextDataError(
                "Business context source is not valid JSON."
            ) from error
        return self._parse_document(document)

    @classmethod
    def _parse_document(cls, document: object) -> tuple[AssetBusinessContext, ...]:
        if not isinstance(document, dict) or set(document) != cls._ROOT_KEYS:
            raise AssetBusinessContextDataError(
                "Business context source must contain only assetBusinessContexts."
            )
        records = document["assetBusinessContexts"]
        if not isinstance(records, list):
            raise AssetBusinessContextDataError(
                "Business context records must be a list."
            )
        contexts = tuple(cls._parse_record(record) for record in records)
        identifiers = [item.canonical_asset_id for item in contexts]
        if len(identifiers) != len(set(identifiers)):
            raise AssetBusinessContextDataError(
                "Business context source contains duplicate canonical assets."
            )
        return contexts

    @classmethod
    def _parse_record(cls, record: object) -> AssetBusinessContext:
        if not isinstance(record, dict) or set(record) != cls._RECORD_KEYS:
            raise AssetBusinessContextDataError(
                "Business context record has an invalid schema."
            )
        try:
            return AssetBusinessContext(
                canonical_asset_id=cls._required_string(record, "canonicalAssetId"),
                business_service=cls._required_string(record, "businessService"),
                environment=BusinessEnvironment(
                    cls._required_string(record, "environment")
                ),
                service_criticality=ServiceCriticality(
                    cls._required_string(record, "serviceCriticality")
                ),
                source_reference=cls._required_string(record, "sourceReference"),
            )
        except (TypeError, ValueError) as error:
            raise AssetBusinessContextDataError(
                "Business context record contains an invalid value."
            ) from error

    @staticmethod
    def _required_string(record: dict[object, object], key: str) -> str:
        value = record[key]
        if not isinstance(value, str) or not value.strip():
            raise AssetBusinessContextDataError(
                f"Business context {key} must be a non-empty string."
            )
        return value.strip()
