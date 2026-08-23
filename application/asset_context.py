from __future__ import annotations

import json
from pathlib import Path

from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)


class AssetContextConfigurationError(ValueError):
    """Raised when the configured asset context source is missing."""


class AssetContextDataError(ValueError):
    """Raised when asset context data is invalid or ambiguous."""


def classify_observed_asset_identifier(
    value: str,
) -> ObservedAssetIdentifier | None:
    """Return a supported typed identifier or no resolvable context key."""
    normalized_value = value.strip()
    if not normalized_value:
        return None

    try:
        return ObservedAssetIdentifier(
            identifier_type=AssetIdentifierType.IP_ADDRESS,
            value=normalized_value,
        )
    except ValueError:
        return None


class AssetContextQueryService:
    """Resolve explicit asset identifiers from one configured JSON source."""

    _ROOT_KEYS = {"assets"}
    _RECORD_KEYS = {
        "identifierType",
        "identifier",
        "canonicalAssetId",
        "assetCriticality",
        "sourceReference",
    }

    def __init__(self, context_path: str | None) -> None:
        self._context_path = context_path

    def resolve(
        self,
        observed_identifier: ObservedAssetIdentifier,
    ) -> AssetContext | None:
        contexts = self._load_contexts()
        matches = [
            context
            for context in contexts
            if context.observed_identifier == observed_identifier
        ]

        if len(matches) > 1:
            raise AssetContextDataError(
                "Asset context source contains an ambiguous identifier."
            )

        return matches[0] if matches else None

    def resolve_canonical_asset(self, canonical_asset_id: str) -> AssetContext | None:
        """Resolve a canonical asset identity from the authoritative source."""
        normalized_id = canonical_asset_id.strip()
        if not normalized_id:
            raise ValueError("Canonical asset ID must not be empty.")
        contexts = self._load_contexts()
        matches = [
            context for context in contexts
            if context.canonical_asset_id == normalized_id
        ]
        if len(matches) > 1:
            raise AssetContextDataError(
                "Asset context source contains an ambiguous canonical asset."
            )
        return matches[0] if matches else None

    def _load_contexts(self) -> tuple[AssetContext, ...]:
        if self._context_path is None or not self._context_path.strip():
            raise AssetContextConfigurationError(
                "ASSET_CONTEXT_PATH is not configured."
            )

        try:
            source_text = Path(self._context_path).read_text(
                encoding="utf-8"
            )
        except OSError as error:
            raise AssetContextConfigurationError(
                "ASSET_CONTEXT_PATH cannot be read."
            ) from error

        try:
            document = json.loads(source_text)
        except json.JSONDecodeError as error:
            raise AssetContextDataError(
                "Asset context source is not valid JSON."
            ) from error

        return self._parse_document(document)

    @classmethod
    def _parse_document(
        cls,
        document: object,
    ) -> tuple[AssetContext, ...]:
        if not isinstance(document, dict) or set(document) != cls._ROOT_KEYS:
            raise AssetContextDataError(
                "Asset context source must contain only an assets list."
            )

        records = document["assets"]

        if not isinstance(records, list):
            raise AssetContextDataError(
                "Asset context assets must be a list."
            )

        return tuple(cls._parse_record(record) for record in records)

    @classmethod
    def _parse_record(cls, record: object) -> AssetContext:
        if not isinstance(record, dict) or set(record) != cls._RECORD_KEYS:
            raise AssetContextDataError(
                "Asset context record has an invalid schema."
            )

        try:
            return AssetContext(
                observed_identifier=ObservedAssetIdentifier(
                    identifier_type=AssetIdentifierType(
                        cls._required_string(record, "identifierType")
                    ),
                    value=cls._required_string(record, "identifier"),
                ),
                canonical_asset_id=cls._required_string(
                    record,
                    "canonicalAssetId",
                ),
                criticality=AssetCriticality(
                    cls._required_string(record, "assetCriticality")
                ),
                source_reference=cls._required_string(
                    record,
                    "sourceReference",
                ),
            )
        except (TypeError, ValueError) as error:
            raise AssetContextDataError(
                "Asset context record contains an invalid value."
            ) from error

    @staticmethod
    def _required_string(record: dict[object, object], key: str) -> str:
        value = record[key]

        if not isinstance(value, str) or not value.strip():
            raise AssetContextDataError(
                f"Asset context {key} must be a non-empty string."
            )

        return value.strip()
