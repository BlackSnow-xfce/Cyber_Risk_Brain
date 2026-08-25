from __future__ import annotations

import json
import os
import tempfile
import threading
import time
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


class HuntHypothesisConflictError(RuntimeError):
    """Raised when a hypothesis identity already exists."""


class HuntHypothesisPersistenceError(RuntimeError):
    """Raised when safe repository persistence cannot complete."""


class HuntHypothesisRepository(Protocol):
    def list(self) -> tuple[HuntHypothesis, ...]:
        ...

    def create(self, hypothesis: HuntHypothesis) -> HuntHypothesis:
        ...


class FileHuntHypothesisRepository:
    """Strict JSON adapter with locked, atomic canonical creation."""

    def __init__(self, path: str | None, *, lock_timeout_seconds: float = 5.0) -> None:
        self._path = path
        self._lock_timeout_seconds = lock_timeout_seconds

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

    def create(self, hypothesis: HuntHypothesis) -> HuntHypothesis:
        if not isinstance(hypothesis, HuntHypothesis):
            raise HuntHypothesisDataError("A canonical Hunt Hypothesis is required.")
        path = self._configured_path()
        if not path.is_file():
            raise HuntHypothesisConfigurationError(
                "HUNT_HYPOTHESIS_REPOSITORY_PATH cannot be read."
            )
        lock = _RepositoryLock(
            path.with_name(f"{path.name}.lock"), self._lock_timeout_seconds
        )
        with lock:
            current = self.list()
            if any(item.hypothesis_id == hypothesis.hypothesis_id for item in current):
                raise HuntHypothesisConflictError(
                    "Hunt Hypothesis identity already exists."
                )
            document = {
                "contract_version": HUNT_HYPOTHESIS_CONTRACT_VERSION,
                "hypotheses": [item.to_dict() for item in (*current, hypothesis)],
            }
            self._atomic_write(path, document)
            persisted = self.list()
            if not persisted or persisted[-1] != hypothesis:
                raise HuntHypothesisPersistenceError(
                    "Persisted Hunt Hypothesis verification failed."
                )
            return persisted[-1]

    @staticmethod
    def _atomic_write(path: Path, document: dict[str, object]) -> None:
        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="\n",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                json.dump(document, temporary, ensure_ascii=False, indent=2)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
            os.replace(temporary_path, path)
            temporary_path = None
            if os.name != "nt":
                directory_fd = os.open(path.parent, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
        except OSError as error:
            raise HuntHypothesisPersistenceError(
                "Hunt Hypothesis repository could not be safely persisted."
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass

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


_PROCESS_LOCKS: dict[Path, threading.Lock] = {}
_PROCESS_LOCKS_GUARD = threading.Lock()


class _RepositoryLock:
    def __init__(self, path: Path, timeout_seconds: float) -> None:
        self._path = path
        self._timeout_seconds = timeout_seconds
        self._handle = None
        with _PROCESS_LOCKS_GUARD:
            self._process_lock = _PROCESS_LOCKS.setdefault(
                path.resolve(), threading.Lock()
            )

    def __enter__(self) -> "_RepositoryLock":
        if not self._process_lock.acquire(timeout=self._timeout_seconds):
            raise HuntHypothesisPersistenceError(
                "Hunt Hypothesis repository lock is unavailable."
            )
        try:
            self._path.parent.mkdir(parents=False, exist_ok=True)
            self._handle = self._path.open("a+b")
            self._ensure_lock_byte()
            deadline = time.monotonic() + self._timeout_seconds
            while True:
                try:
                    self._lock_handle()
                    return self
                except (BlockingIOError, OSError) as error:
                    if time.monotonic() >= deadline:
                        raise HuntHypothesisPersistenceError(
                            "Hunt Hypothesis repository lock is unavailable."
                        ) from error
                    time.sleep(0.05)
        except Exception:
            self._close()
            self._process_lock.release()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if self._handle is not None:
                self._unlock_handle()
        finally:
            self._close()
            self._process_lock.release()

    def _ensure_lock_byte(self) -> None:
        assert self._handle is not None
        self._handle.seek(0, os.SEEK_END)
        if self._handle.tell() == 0:
            self._handle.write(b"\0")
            self._handle.flush()
        self._handle.seek(0)

    def _lock_handle(self) -> None:
        assert self._handle is not None
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock_handle(self) -> None:
        assert self._handle is not None
        self._handle.seek(0)
        if os.name == "nt":
            import msvcrt

            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)

    def _close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
