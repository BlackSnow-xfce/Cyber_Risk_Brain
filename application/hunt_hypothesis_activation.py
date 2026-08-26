from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from application.hunt_hypotheses import (
    HuntHypothesisActivationRecoveryRequiredError,
    HuntHypothesisActivationRolledBackError,
    HuntHypothesisRepository,
    HuntHypothesisRepositoryNotFoundError,
    HuntHypothesisStateConflictError,
)
from application.local_operator import (
    AuthenticatedPrincipal,
    AuthorizationDecision,
    HuntHypothesisActivationAuthority,
    LocalOperatorAuthorizationError,
)
from core.threat_hunting import HuntHypothesis, HuntHypothesisStatus


class HuntHypothesisActivationValidationError(ValueError):
    pass


class HuntHypothesisActivationAuditError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class HuntHypothesisActivationInput:
    hypothesis_id: str
    expected_status: HuntHypothesisStatus


@dataclass(frozen=True, slots=True)
class HuntHypothesisActivationResult:
    hypothesis: HuntHypothesis
    authorization: AuthorizationDecision


class HuntHypothesisActivationAuditSink(Protocol):
    def append(self, event: dict[str, str | None]) -> None:
        ...


_AUDIT_LOCKS: dict[Path, threading.Lock] = {}
_AUDIT_LOCKS_GUARD = threading.Lock()
_fsync_audit = os.fsync


class FileHuntHypothesisActivationAuditSink:
    def __init__(self, path: str | None) -> None:
        if path is None or not path.strip():
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation audit is not configured."
            )
        self._path = Path(path)
        with _AUDIT_LOCKS_GUARD:
            self._lock = _AUDIT_LOCKS.setdefault(
                self._path.resolve(), threading.Lock()
            )

    def append(self, event: dict[str, str | None]) -> None:
        temporary_path: Path | None = None
        try:
            payload = (
                json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n"
            ).encode("utf-8")
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._lock:
                existing = self._path.read_bytes() if self._path.exists() else b""
                if existing and not existing.endswith(b"\n"):
                    raise HuntHypothesisActivationAuditError(
                        "Hunt Hypothesis activation audit is malformed."
                    )
                with tempfile.NamedTemporaryFile(
                    mode="w+b",
                    dir=self._path.parent,
                    prefix=f".{self._path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as audit:
                    temporary_path = Path(audit.name)
                    audit.write(existing)
                    audit.write(payload)
                    audit.flush()
                    _fsync_audit(audit.fileno())
                os.replace(temporary_path, self._path)
                temporary_path = None
        except (OSError, TypeError, ValueError) as error:
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation audit could not be persisted."
            ) from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError:
                    pass


class HuntHypothesisActivationService:
    def __init__(
        self,
        repository: HuntHypothesisRepository,
        audit_sink: HuntHypothesisActivationAuditSink,
        *,
        authority: HuntHypothesisActivationAuthority | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        attempt_id_generator: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._repository = repository
        self._audit_sink = audit_sink
        self._authority = authority or HuntHypothesisActivationAuthority()
        self._clock = clock
        self._attempt_id_generator = attempt_id_generator

    def activate(
        self,
        request: HuntHypothesisActivationInput,
        principal: AuthenticatedPrincipal,
    ) -> HuntHypothesisActivationResult:
        timestamp = self._timestamp()
        attempt_id = self._attempt_id()
        decision = self._authority.evaluate(principal)
        if decision.outcome != "allowed":
            self._audit(
                request,
                principal.principal_id,
                timestamp,
                attempt_id,
                "terminal",
                "denied",
                "authorization_denied",
                None,
                None,
            )
            raise LocalOperatorAuthorizationError(
                "The authenticated principal is not authorized."
            )
        if (
            not isinstance(request, HuntHypothesisActivationInput)
            or safe_hypothesis_audit_id(request.hypothesis_id) is None
            or request.expected_status is not HuntHypothesisStatus.DRAFT
        ):
            self._audit(
                request,
                principal.principal_id,
                timestamp,
                attempt_id,
                "terminal",
                "rejected",
                "invalid_expected_state",
                None,
                None,
            )
            raise HuntHypothesisActivationValidationError(
                "Hunt Hypothesis activation input is invalid."
            )
        self._audit(
            request,
            principal.principal_id,
            timestamp,
            attempt_id,
            "attempt",
            "authorized",
            "authorized_attempt",
            None,
            None,
        )
        try:
            hypothesis = self._repository.activate(
                request.hypothesis_id,
                request.expected_status,
                lambda persisted: self._audit(
                    request,
                    principal.principal_id,
                    timestamp,
                    attempt_id,
                    "terminal",
                    "activated",
                    "draft_activated_for_investigation",
                    HuntHypothesisStatus.DRAFT,
                    persisted.status,
                ),
            )
        except HuntHypothesisActivationRolledBackError as error:
            self._audit(
                request,
                principal.principal_id,
                timestamp,
                attempt_id,
                "terminal",
                "rolled_back",
                "terminal_audit_failed_rollback_verified",
                HuntHypothesisStatus.DRAFT,
                None,
            )
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation audit could not be finalized."
            ) from error
        except HuntHypothesisActivationRecoveryRequiredError as error:
            self._audit(
                request,
                principal.principal_id,
                timestamp,
                attempt_id,
                "terminal",
                "reconciliation_required",
                "activation_recovery_unverified",
                None,
                None,
            )
            raise
        except Exception as error:
            if isinstance(error, HuntHypothesisActivationAuditError):
                raise
            reason = self._safe_reason(error)
            current_status = (
                error.actual_status
                if isinstance(error, HuntHypothesisStateConflictError)
                else None
            )
            self._audit(
                request,
                principal.principal_id,
                timestamp,
                attempt_id,
                "terminal",
                "rejected",
                reason,
                current_status,
                None,
            )
            raise
        return HuntHypothesisActivationResult(hypothesis, decision)

    def _timestamp(self) -> datetime:
        timestamp = self._clock()
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation clock is invalid."
            )
        return timestamp

    def _audit(
        self,
        request: HuntHypothesisActivationInput,
        principal_id: str | None,
        timestamp: datetime,
        attempt_id: str,
        phase: str,
        outcome: str,
        reason: str,
        current_status: HuntHypothesisStatus | None,
        resulting_status: HuntHypothesisStatus | None,
    ) -> None:
        expected_status = getattr(request, "expected_status", None)
        self._audit_sink.append(
            {
                "authorization_outcome": (
                    "denied" if outcome == "denied" else "allowed"
                ),
                "attempt_id": attempt_id,
                "commit_state": (
                    "committed"
                    if outcome == "activated"
                    else "pending"
                    if phase == "attempt"
                    else "not_committed"
                    if outcome in {"denied", "rejected", "rolled_back"}
                    else "reconciliation_required"
                ),
                "current_status": (
                    current_status.value if current_status is not None else None
                ),
                "expected_status": (
                    expected_status.value
                    if isinstance(expected_status, HuntHypothesisStatus)
                    else None
                ),
                "hypothesis_id": safe_hypothesis_audit_id(
                    getattr(request, "hypothesis_id", None)
                ),
                "mutation_state": (
                    "persisted"
                    if outcome == "activated"
                    else "not_started"
                    if phase == "attempt" or outcome in {"denied", "rejected"}
                    else "rolled_back"
                    if outcome == "rolled_back"
                    else "unknown"
                ),
                "operation": "hunt_hypothesis:activate",
                "outcome": outcome,
                "phase": phase,
                "principal_id": principal_id,
                "reason": reason,
                "resulting_status": (
                    resulting_status.value if resulting_status is not None else None
                ),
                "timestamp": timestamp.isoformat(),
            }
        )

    def _attempt_id(self) -> str:
        attempt_id = self._attempt_id_generator()
        if not isinstance(attempt_id, str) or not attempt_id.strip():
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation attempt identity is invalid."
            )
        return attempt_id

    @staticmethod
    def _safe_reason(error: Exception) -> str:
        if isinstance(error, HuntHypothesisRepositoryNotFoundError):
            return "hypothesis_not_found"
        if isinstance(error, HuntHypothesisStateConflictError):
            return "expected_state_mismatch"
        return "repository_or_integrity_rejected"


class HuntHypothesisActivationAttemptAuditor:
    """Writes one terminal record for requests rejected before the service."""

    def __init__(
        self,
        audit_sink: HuntHypothesisActivationAuditSink,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        attempt_id_generator: Callable[[], str] = lambda: str(uuid.uuid4()),
    ) -> None:
        self._audit_sink = audit_sink
        self._clock = clock
        self._attempt_id_generator = attempt_id_generator

    def reject(
        self,
        *,
        hypothesis_id: str | None,
        principal_id: str | None,
        reason: str,
        expected_status: HuntHypothesisStatus | None = None,
        authorization_outcome: str = "not_evaluated",
    ) -> None:
        timestamp = self._clock()
        attempt_id = self._attempt_id_generator()
        if (
            not isinstance(timestamp, datetime)
            or timestamp.tzinfo is None
            or not isinstance(attempt_id, str)
            or not attempt_id.strip()
        ):
            raise HuntHypothesisActivationAuditError(
                "Hunt Hypothesis activation audit context is invalid."
            )
        self._audit_sink.append(
            {
                "authorization_outcome": authorization_outcome,
                "attempt_id": attempt_id,
                "commit_state": "not_committed",
                "current_status": None,
                "expected_status": (
                    expected_status.value if expected_status is not None else None
                ),
                "hypothesis_id": safe_hypothesis_audit_id(hypothesis_id),
                "mutation_state": "not_started",
                "operation": "hunt_hypothesis:activate",
                "outcome": "rejected",
                "phase": "terminal",
                "principal_id": principal_id,
                "reason": reason,
                "resulting_status": None,
                "timestamp": timestamp.isoformat(),
            }
        )


_CANONICAL_HYPOTHESIS_ID = re.compile(
    r"^hypothesis-[A-Za-z0-9][A-Za-z0-9._-]{0,127}$"
)


def safe_hypothesis_audit_id(value: object) -> str | None:
    """Return only a structurally canonical identifier for audit projection."""

    if not isinstance(value, str) or not _CANONICAL_HYPOTHESIS_ID.fullmatch(value):
        return None
    return value
