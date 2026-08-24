from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Protocol

from core.threat_hunting import (
    HUNT_HYPOTHESIS_CONTRACT_VERSION,
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


_ROOT_KEYS = {"contract_version", "hypotheses"}
_HYPOTHESIS_KEYS = {
    "hypothesis_id",
    "title",
    "statement",
    "status",
    "created_at",
    "created_by",
    "target_references",
    "threat_references",
    "rationale",
    "contract_version",
}
_REFERENCE_KEYS = {"reference_type", "reference_id"}


class HuntHypothesisConfigurationError(ValueError):
    """Raised when no readable Hunt Hypothesis repository is configured."""


class HuntHypothesisDataError(ValueError):
    """Raised when persisted Hunt Hypothesis data is not canonical."""


class HuntHypothesisRepository(Protocol):
    def list(self) -> tuple[HuntHypothesis, ...]:
        ...


class FileHuntHypothesisRepository:
    """Strict read-only JSON adapter for HuntHypothesis 1.0."""

    def __init__(self, path: str | None) -> None:
        self._path = path

    def list(self) -> tuple[HuntHypothesis, ...]:
        path = self._configured_path()
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeError as error:
            raise HuntHypothesisDataError(
                "Hunt Hypothesis repository is not valid UTF-8 JSON."
            ) from error
        except OSError as error:
            raise HuntHypothesisConfigurationError(
                "HUNT_HYPOTHESIS_REPOSITORY_PATH cannot be read."
            ) from error

        try:
            document = json.loads(source)
        except json.JSONDecodeError as error:
            raise HuntHypothesisDataError(
                "Hunt Hypothesis repository is not valid UTF-8 JSON."
            ) from error

        if not isinstance(document, dict) or set(document) != _ROOT_KEYS:
            raise HuntHypothesisDataError(
                "Hunt Hypothesis repository has an invalid schema."
            )
        if document["contract_version"] != HUNT_HYPOTHESIS_CONTRACT_VERSION:
            raise HuntHypothesisDataError(
                "Hunt Hypothesis repository contract version is unsupported."
            )
        records = document["hypotheses"]
        if not isinstance(records, list):
            raise HuntHypothesisDataError("Hypotheses must be a list.")

        hypotheses = tuple(self._parse_hypothesis(record) for record in records)
        hypothesis_ids = [item.hypothesis_id for item in hypotheses]
        if len(set(hypothesis_ids)) != len(hypothesis_ids):
            raise HuntHypothesisDataError(
                "Hunt Hypothesis repository contains duplicate hypothesis IDs."
            )
        return hypotheses

    def _configured_path(self) -> Path:
        if self._path is None or not self._path.strip():
            raise HuntHypothesisConfigurationError(
                "HUNT_HYPOTHESIS_REPOSITORY_PATH is not configured."
            )
        return Path(self._path)

    @classmethod
    def _parse_hypothesis(cls, value: object) -> HuntHypothesis:
        if not isinstance(value, dict) or set(value) != _HYPOTHESIS_KEYS:
            raise HuntHypothesisDataError(
                "Hunt Hypothesis record has an invalid schema."
            )
        try:
            return HuntHypothesis(
                hypothesis_id=cls._string(value["hypothesis_id"], "hypothesis_id"),
                title=cls._string(value["title"], "title"),
                statement=cls._string(value["statement"], "statement"),
                status=HuntHypothesisStatus(
                    cls._string(value["status"], "status")
                ),
                created_at=cls._timestamp(value["created_at"]),
                created_by=cls._string(value["created_by"], "created_by"),
                target_references=cls._references(
                    value["target_references"], "target_references"
                ),
                threat_references=cls._references(
                    value["threat_references"], "threat_references"
                ),
                rationale=cls._string(value["rationale"], "rationale"),
                contract_version=cls._string(
                    value["contract_version"], "contract_version"
                ),
            )
        except (TypeError, ValueError) as error:
            if isinstance(error, HuntHypothesisDataError):
                raise
            raise HuntHypothesisDataError(
                "Hunt Hypothesis record contains an invalid value."
            ) from error

    @classmethod
    def _references(
        cls, value: object, label: str
    ) -> tuple[HuntHypothesisReference, ...]:
        if not isinstance(value, list):
            raise HuntHypothesisDataError(f"{label} must be a list.")
        references: list[HuntHypothesisReference] = []
        for item in value:
            if not isinstance(item, dict) or set(item) != _REFERENCE_KEYS:
                raise HuntHypothesisDataError(
                    f"{label} contains an invalid reference."
                )
            references.append(
                HuntHypothesisReference(
                    reference_type=HuntHypothesisReferenceType(
                        cls._string(item["reference_type"], "reference_type")
                    ),
                    reference_id=cls._string(item["reference_id"], "reference_id"),
                )
            )
        return tuple(references)

    @staticmethod
    def _string(value: object, label: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise HuntHypothesisDataError(f"{label} must be a non-empty string.")
        return value.strip()

    @classmethod
    def _timestamp(cls, value: object) -> datetime:
        raw = cls._string(value, "created_at")
        try:
            timestamp = datetime.fromisoformat(raw)
        except ValueError as error:
            raise HuntHypothesisDataError(
                "created_at must be an ISO-8601 timestamp."
            ) from error
        if timestamp.utcoffset() is None:
            raise HuntHypothesisDataError("created_at must be timezone-aware.")
        return timestamp


class HuntHypothesisQueryService:
    """Read canonical hypotheses without introducing write authority."""

    def __init__(self, repository: HuntHypothesisRepository) -> None:
        self._repository = repository

    def list(self) -> tuple[HuntHypothesis, ...]:
        return self._repository.list()
