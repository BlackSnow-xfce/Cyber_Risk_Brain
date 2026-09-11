"""Explicit terminal recovery. No verifier is trusted merely by appearing in Git."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import threading
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from .contracts import (
    ExecutionStatus,
    ProductOwnerGateDependencyAuthorityV1, ProductOwnerGateDependencyRecoveryAuthorityV1,
    ProductOwnerGateDependencyResult, ProductOwnerGateDependencyState, canonical_digest, utc_now,
)
from .runtime import LocalRuntimeStore, _sync_parent


_held_locks = threading.local()
EVENTS = ("AUTHORIZED", "RESERVED", "LAUNCH_INTENT", "STARTED", "RESULT_RECORDED", "REVIEWED", "TERMINAL", "BLOCKED")


@contextmanager
def dependency_consumption_lock(root: Path):
    """Share one cross-process boundary with ordinary and bootstrap consumption."""
    from .watcher_runtime import WatcherRuntimeLock

    key = str(root.resolve())
    held = getattr(_held_locks, "paths", set())
    if key in held:
        yield
        return
    lock = WatcherRuntimeLock(root / "gate-dependency-consumption.lock")
    if not lock.acquire():
        raise RuntimeError("dependency consumption is already active")
    _held_locks.paths = held | {key}
    try:
        yield
    finally:
        _held_locks.paths = held
        lock.release()


@dataclass(frozen=True, slots=True)
class VerifiedGateDependencyRecoveryEvidence:
    """Returned only by an independently authenticated evidence boundary.

    The verifier must search configured historical stores, verify the Product
    Owner's recovery permission (not parent acceptance), inspect live processes
    and residual workspaces/refs, and authenticate advancement approvals.
    Inbox data must never be deserialized into this trusted result.
    """

    proposal_digest: str
    product_owner_decision_digest: str
    evidence_digest: str
    advancement_evidence_digest: str
    predecessor_execution_id: str
    verifier_identity: str
    product_owner_identity: str
    permission: str
    approved: bool
    approved_advancement: bool
    mode: str
    pre_launch_failure_proven: bool
    no_active_process: bool
    residuals_clean: bool
    inventory_digest: str
    result_digest: str | None
    attempt_digest: str | None
    execution_store_roots: tuple[Path, ...]
    verified_at: datetime
    valid_until: datetime


class GateDependencyRecoveryEvidenceVerifier(Protocol):
    def verify(
        self, authority: ProductOwnerGateDependencyRecoveryAuthorityV1, *,
        predecessor: ProductOwnerGateDependencyAuthorityV1,
        source: ProductOwnerGateDependencyAuthorityV1,
    ) -> VerifiedGateDependencyRecoveryEvidence: ...


def execution_terms_digest(source: ProductOwnerGateDependencyAuthorityV1) -> str:
    return canonical_digest({name: getattr(source, name) for name in (
        "purpose", "allowed_scope", "prohibited_actions", "validation_requirements", "acceptance_criteria",
    )})


class GateDependencyRecoveryJournal:
    def __init__(self, store: LocalRuntimeStore):
        self.store = store
        self.root = store.root / "gate-dependency-recovery"

    def reservations(self) -> tuple[dict[str, object], ...]:
        values = []
        for path in sorted((self.root / "reservations").glob("*.json")):
            value = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or set(value) != {
                "reservation_id", "recovery_authority_id", "predecessor_authority_id",
                "predecessor_execution_id", "execution_source_authority_id", "execution_id", "reserved_at",
            }:
                raise ValueError("malformed recovery reservation")
            expected = canonical_digest((value["predecessor_authority_id"], value["predecessor_execution_id"]))
            if path.stem != expected or value["reservation_id"] != expected:
                raise ValueError("recovery reservation identity mismatch")
            values.append(value)
        return tuple(values)

    def reserve(self, authority: ProductOwnerGateDependencyRecoveryAuthorityV1) -> dict[str, object]:
        with dependency_consumption_lock(self.store.root):
            # This lane admits no concurrent or automatic follow-on recovery.
            if self.reservations():
                raise RuntimeError("recovery reservation already exists; explicit assessment required")
            key = canonical_digest((authority.predecessor_authority_id, authority.predecessor_execution_id))
            value = dict(reservation_id=key, recovery_authority_id=authority.authority_id,
                         predecessor_authority_id=authority.predecessor_authority_id,
                         predecessor_execution_id=authority.predecessor_execution_id,
                         execution_source_authority_id=authority.execution_source_authority_id,
                         execution_id=str(uuid4()), reserved_at=utc_now().isoformat())
            path = self.root / "reservations" / f"{key}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(value, sort_keys=True) + "\n")
                stream.flush(); os.fsync(stream.fileno())
            _sync_parent(path.parent)
            if json.loads(path.read_text(encoding="utf-8")) != value:
                raise RuntimeError("recovery reservation verification failed")
            return value

    def event(self, authority: ProductOwnerGateDependencyRecoveryAuthorityV1, kind: str,
              *, execution_id: str | None = None, reason: str = "", evidence_digest: str | None = None) -> None:
        if kind not in EVENTS or len(reason) > 256 or "\n" in reason or "\r" in reason:
            raise ValueError("invalid recovery event")
        directory = self.root / "events" / authority.authority_id
        sequence = len(tuple(directory.glob("*.json")))
        value = dict(recovery_authority_id=authority.authority_id,
                     predecessor_authority_id=authority.predecessor_authority_id,
                     predecessor_execution_id=authority.predecessor_execution_id,
                     execution_source_authority_id=authority.execution_source_authority_id,
                     execution_id=execution_id, kind=kind, sequence=sequence,
                     timestamp=utc_now().isoformat(), reason=reason, evidence_digest=evidence_digest)
        self.store._persist_immutable(directory / f"{sequence:06d}.json", json.dumps(value, sort_keys=True), str(sequence))

    def status(self, authority_id: str) -> dict[str, object] | None:
        if len(authority_id) != 64 or any(c not in "0123456789abcdef" for c in authority_id):
            raise ValueError("invalid recovery identity")
        paths = sorted((self.root / "events" / authority_id).glob("*.json"))
        return json.loads(paths[-1].read_text(encoding="utf-8")) if paths else None


class TerminalGateDependencyRecovery:
    def __init__(self, runner, verifier: GateDependencyRecoveryEvidenceVerifier | None = None):
        self.runner, self.verifier = runner, verifier
        self.journal = GateDependencyRecoveryJournal(runner.store)

    def _snapshot(self, folder: str, identifier: str, expected_digest: str) -> dict[str, object]:
        path = self.runner.store.root / folder / f"{identifier}.json"
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_digest:
            raise ValueError("predecessor evidence digest mismatch")
        value = json.loads(raw)
        wrapper = "product_owner_gate_dependency_claim" if folder.endswith("claims") else "product_owner_gate_dependency_status"
        if not isinstance(value, dict) or set(value) != {wrapper}:
            raise ValueError("malformed predecessor evidence")
        record = value[wrapper]
        required = ({"authority_id", "claimed_at", "dependency_id", "execution_id", "parent_task_id", "state"}
                    if folder.endswith("claims") else
                    {"authority_id", "architect_result_id", "dependency_id", "execution_id", "reason", "state", "updated_at"})
        if not isinstance(record, dict) or set(record) != required:
            raise ValueError("malformed predecessor record")
        return record

    @staticmethod
    def _same_execution_assessment(original, refreshed) -> None:
        if any(getattr(original, name) != getattr(refreshed, name) for name in (
            "inventory_digest", "mode", "result_digest", "attempt_digest", "execution_store_roots",
        )):
            raise ValueError("execution evidence changed during recovery authorization")

    def validate(self, authority, items):
        now = utc_now()
        if not authority.issued_at <= now < authority.expires_at:
            raise ValueError("recovery authority is not current")
        by_id = {item.contract_id: item.contract for item in items}
        predecessor = by_id.get(authority.predecessor_authority_id)
        source = by_id.get(authority.execution_source_authority_id)
        if not isinstance(predecessor, ProductOwnerGateDependencyAuthorityV1) or not isinstance(source, ProductOwnerGateDependencyAuthorityV1):
            raise ValueError("recovery predecessor or source unavailable")
        if predecessor.expected_id() != authority.predecessor_authority_digest or source.expected_id() != authority.execution_source_digest:
            raise ValueError("recovery source substitution")
        for name in ("parent_task_id", "dependency_id", "repository_id", "git_common_id", "repository_remote_id", "branch"):
            if getattr(predecessor, name) != getattr(authority, name) or getattr(source, name) != getattr(authority, name):
                raise ValueError("recovery identity binding mismatch")
        if predecessor.expected_head != authority.original_expected_head or source.expected_head != authority.expected_head:
            raise ValueError("recovery head binding mismatch")
        if execution_terms_digest(source) != authority.execution_terms_digest or execution_terms_digest(predecessor) != authority.execution_terms_digest:
            raise ValueError("recovery execution terms changed")
        claimed = [item.contract_id for item in items if isinstance(item.contract, ProductOwnerGateDependencyAuthorityV1)
                   and self.runner.store.product_owner_gate_dependency_claimed(item.contract_id)]
        if claimed != [authority.predecessor_authority_id]:
            raise ValueError("conflicting dependency claim")
        claim = self._snapshot("product-owner-gate-dependency-claims", authority.predecessor_authority_id, authority.predecessor_claim_digest)
        terminal = self._snapshot("product-owner-gate-dependency-status", authority.predecessor_authority_id, authority.terminal_status_digest)
        for value in (claim, terminal):
            if value.get("authority_id") != authority.predecessor_authority_id or value.get("execution_id") != authority.predecessor_execution_id or value.get("dependency_id") != authority.dependency_id:
                raise ValueError("predecessor execution evidence mismatch")
        if claim.get("state") != "CONSUMED" or claim.get("parent_task_id") != authority.parent_task_id:
            raise ValueError("predecessor claim is not consumed")
        if terminal.get("state") != "BLOCKED" or terminal.get("reason") != authority.terminal_reason or terminal.get("architect_result_id") is not None:
            raise ValueError("predecessor terminal state mismatch")
        self.runner._validate(source)
        if source.issued_at > now or self.runner._parent_snapshot(authority.parent_task_id) != authority.parent_lifecycle_digest:
            raise ValueError("recovery parent lifecycle changed")
        if self.runner._git_at(self.runner.repository.root, "status", "--porcelain=v1", "--untracked-files=all"):
            raise ValueError("recovery baseline is not clean")
        subprocess.run(("git", "merge-base", "--is-ancestor", authority.original_expected_head, authority.expected_head),
                       cwd=self.runner.repository.root, check=True, capture_output=True)
        if self.verifier is None:
            raise PermissionError("trusted recovery evidence verifier is not configured")
        evidence = self.verifier.verify(authority, predecessor=predecessor, source=source)
        if not isinstance(evidence, VerifiedGateDependencyRecoveryEvidence):
            raise PermissionError("untrusted recovery evidence")
        now = utc_now()
        for name in ("product_owner_decision_digest", "evidence_digest", "advancement_evidence_digest", "predecessor_execution_id"):
            if getattr(evidence, name) != getattr(authority, name):
                raise PermissionError("recovery evidence binding mismatch")
        if evidence.proposal_digest != authority.proposal_digest() or evidence.permission != "RECOVER_GATE_DEPENDENCY" or evidence.approved is not True:
            raise PermissionError("Product Owner did not authorize this recovery proposal")
        if not evidence.verifier_identity or not evidence.product_owner_identity or evidence.approved_advancement is not True:
            raise PermissionError("recovery authorization provenance is missing")
        if evidence.verified_at.tzinfo is None or evidence.valid_until.tzinfo is None or not evidence.verified_at <= now < evidence.valid_until:
            raise PermissionError("recovery evidence is stale")
        if (now - evidence.verified_at).total_seconds() > 60 or now >= authority.expires_at or now >= source.expires_at:
            raise PermissionError("recovery assessment or authority expired during verification")
        if evidence.no_active_process is not True or evidence.residuals_clean is not True:
            raise ValueError("UNKNOWN_EXECUTION_OUTCOME: active process or unexplained residuals")
        if len(evidence.inventory_digest) != 64 or any(c not in "0123456789abcdef" for c in evidence.inventory_digest):
            raise ValueError("residual inventory evidence is missing")
        if evidence.mode == "PRE_LAUNCH_FAILURE":
            if evidence.pre_launch_failure_proven is not True or evidence.result_digest is not None or evidence.attempt_digest is not None:
                raise ValueError("UNKNOWN_EXECUTION_OUTCOME: pre-launch failure is not proven")
        elif evidence.mode == "PERSISTED_FAILURE":
            if not evidence.result_digest or not evidence.attempt_digest:
                raise ValueError("UNKNOWN_EXECUTION_OUTCOME: result and attempt evidence required")
        else:
            raise ValueError("UNKNOWN_EXECUTION_OUTCOME: missing execution result")
        # The verifier supplies authenticated store locations, never the authority.
        if not evidence.execution_store_roots or any(not p.is_absolute() for p in evidence.execution_store_roots):
            raise ValueError("authoritative execution stores were not assessed")
        roots = set(evidence.execution_store_roots) | {self.runner.store.root}
        identifier = authority.predecessor_execution_id
        result_paths = [p / "results" / f"{identifier}.json" for p in roots if (p / "results" / f"{identifier}.json").exists()]
        attempt_paths = [p / "execution-attempts" / f"{identifier}.json" for p in roots if (p / "execution-attempts" / f"{identifier}.json").exists()]
        if evidence.mode == "PRE_LAUNCH_FAILURE":
            if result_paths or attempt_paths or any((p / "execution-heartbeats" / f"{identifier}.json").exists() for p in roots):
                raise ValueError("UNKNOWN_EXECUTION_OUTCOME: contradictory execution evidence")
        else:
            if len(result_paths) != 1 or len(attempt_paths) != 1:
                raise ValueError("UNKNOWN_EXECUTION_OUTCOME: missing or ambiguous persisted evidence")
            result_path, attempt_path = result_paths[0], attempt_paths[0]
            if hashlib.sha256(result_path.read_bytes()).hexdigest() != evidence.result_digest or hashlib.sha256(attempt_path.read_bytes()).hexdigest() != evidence.attempt_digest:
                raise ValueError("execution evidence digest mismatch")
            attempt = LocalRuntimeStore(attempt_path.parent.parent).execution_attempt(identifier)
            result = json.loads(result_path.read_text(encoding="utf-8"))["codex_execution_result"]
            if (attempt.contract_id != authority.predecessor_authority_id or attempt.task_id != authority.dependency_id
                    or attempt.expected_head != authority.original_expected_head
                    or attempt.namespace != "product-owner-gate-dependency"
                    or attempt.scope_digest != canonical_digest({"allowed": predecessor.allowed_scope, "prohibited": predecessor.prohibited_actions})
                    or result.get("execution_id") != identifier or result.get("task_id") != authority.dependency_id
                    or result.get("start_commit") != authority.original_expected_head
                    or ExecutionStatus(result.get("status")) in {ExecutionStatus.SUCCESS, ExecutionStatus.RUNNING}):
                raise ValueError("persisted failure does not bind predecessor execution")
        return source, evidence

    def run_once(self, authority, items) -> ProductOwnerGateDependencyResult:
        execution_id = None
        try:
            with dependency_consumption_lock(self.runner.store.root):
                if self.journal.reservations():
                    raise RuntimeError("recovery already reserved; automatic relaunch prohibited")
                source, evidence = self.validate(authority, items)
                assessment = json.dumps(asdict(evidence), default=str, sort_keys=True)
                self.runner.store._persist_immutable(self.journal.root / "assessments" / f"{canonical_digest(assessment)}.json", assessment, authority.evidence_digest)
                self.journal.event(authority, "AUTHORIZED", evidence_digest=authority.evidence_digest)
                source, refreshed = self.validate(authority, self.runner.inbox.pending())
                self._same_execution_assessment(evidence, refreshed)
                reservation = self.journal.reserve(authority)
                execution_id = reservation["execution_id"]
                self.journal.event(authority, "RESERVED", execution_id=execution_id)
                from .trigger_publisher import ProductOwnerGateDependencyRunner

                coordinator = self

                class RecoveryExecution(ProductOwnerGateDependencyRunner):
                    def _claim_dependency(self, value, identifier):
                        # The durable recovery reservation is the new claim.
                        if identifier != execution_id or value.authority_id != authority.execution_source_authority_id:
                            raise ValueError("recovery reservation binding mismatch")

                    def _execution_authority_id(self, value):
                        return authority.authority_id

                    def _execution_authority_digest(self, value):
                        return authority.expected_id()

                    def _workspace_key(self, value):
                        return authority.authority_id

                    def _run_authorized(self, runner, request, value):
                        return runner.execute_authorized(
                            request, contract_id=authority.authority_id,
                            namespace="product-owner-gate-dependency-recovery",
                            on_attempt_persisted=lambda: self._execution_event("STARTED"),
                        )

                    def _dependency_status(self, value, state, reason, **metadata):
                        # Recovery has its own immutable event/status lineage.
                        return None

                    def _execution_event(self, kind, **metadata):
                        if kind == "LAUNCH_INTENT":
                            _, refreshed = coordinator.validate(authority, coordinator.runner.inbox.pending())
                            coordinator._same_execution_assessment(evidence, refreshed)
                        coordinator.journal.event(authority, kind, execution_id=execution_id,
                                                  evidence_digest=metadata.get("evidence_digest"))

                worker = RecoveryExecution(self.runner.repository, runtime_root=self.runner.inbox.root.parent,
                                           architect=self.runner.architect, timeout_seconds=self.runner.timeout_seconds)
                result = worker._execute_dependency(source, execution_id)
                self.journal.event(authority, "TERMINAL" if result.state is ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING else "BLOCKED",
                                   execution_id=execution_id, reason=result.reason or "")
                return result
        except Exception as exc:
            reason = str(exc) if isinstance(exc, (ValueError, PermissionError, RuntimeError)) else type(exc).__name__
            reason = " ".join(reason.split())[:256]
            # A reservation remains consumed even if an audit write fails.
            try:
                with dependency_consumption_lock(self.runner.store.root):
                    previous = self.journal.status(authority.authority_id)
                    if previous is None or previous.get("kind") != "BLOCKED" or previous.get("reason") != reason:
                        self.journal.event(authority, "BLOCKED", execution_id=execution_id, reason=reason)
            except (OSError, ValueError, RuntimeError):
                reason = "recovery audit unavailable; automatic execution prohibited"
            return ProductOwnerGateDependencyResult(authority.authority_id, authority.dependency_id,
                                                    ProductOwnerGateDependencyState.BLOCKED,
                                                    execution_id=execution_id, reason=reason)
