"""Explicit, fail-closed trigger boundary for one ready AIDP execution."""

from __future__ import annotations

import json
import inspect
import threading
from dataclasses import asdict
from datetime import datetime
from dataclasses import replace
from enum import Enum
from pathlib import Path
from typing import Protocol

from .contracts import (
    AIDPState,
    AuditEvent,
    CodexExecutionRequest,
    CodexExecutionResult,
    OrchestrationDecision,
    RunnerResult,
    RunnerStatus,
    ExecutionStatus, ExecutionAttemptV1, ExecutionHeartbeatV1,
    ExecutionSupervisionFailureV1, canonical_digest,
    ScopeCompliance,
    utc_now,
)
from .executor import CodexExecutionService
from .operator_stream import ActivitySink
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore


class ExecutionService(Protocol):
    def execute(self, request: CodexExecutionRequest,
                supervision_event: threading.Event | None = None) -> CodexExecutionResult: ...


class RuntimeStore(Protocol):
    def persist_result(self, result: CodexExecutionResult) -> Path: ...

    def append_audit(self, event: AuditEvent) -> Path: ...
    def persist_execution_attempt(self, attempt: ExecutionAttemptV1) -> Path: ...
    def persist_execution_heartbeat(self, heartbeat: ExecutionHeartbeatV1) -> Path: ...
    def persist_supervision_failure(self, failure: ExecutionSupervisionFailureV1) -> Path: ...


class AIDPRunner:
    """Runs one eligible task; authority remains in repository inspection.

    V1 guarantees single execution only within this local repository/runner
    context. It does not provide global or distributed exclusivity.
    """

    def __init__(
        self,
        repository: AIDPRepository,
        *,
        execution_service: ExecutionService | None = None,
        runtime_store: RuntimeStore | None = None,
        timeout_seconds: float = 900.0,
        activity_sink: ActivitySink | None = None,
    ):
        self.repository = repository
        self.execution_service = execution_service or CodexExecutionService(
            repository_root=repository.root,
            timeout_seconds=timeout_seconds,
            activity_sink=activity_sink,
        )
        self.runtime_store = runtime_store or LocalRuntimeStore.for_repository(repository.root)
        self._contract_context: tuple[str, int, int, tuple[str, ...] | None] | None = None

    def authorize_contract_context(self, contract_id: str, *, attempt_ordinal: int, retry_budget: int,
                                   allowed_scope: tuple[str, ...] | None = None) -> None:
        self._contract_context = (contract_id, attempt_ordinal, retry_budget, allowed_scope)

    def execute_authorized(
        self, request: CodexExecutionRequest, *, contract_id: str, namespace: str,
    ) -> CodexExecutionResult:
        """Execute an already-validated non-task authority with normal durable supervision."""
        attempt = ExecutionAttemptV1(
            "aidp-execution-attempt-v1", request.execution_id, contract_id, request.task_id,
            namespace, canonical_digest(str(self.repository.root.resolve()).lower()),
            request.expected_head,
            canonical_digest({"allowed": request.allowed_scope, "prohibited": request.prohibited_actions}),
            0, 0, utc_now(),
        )
        self.runtime_store.persist_execution_attempt(attempt)
        stop_heartbeat, supervision_failure = threading.Event(), threading.Event()
        heartbeat_failure: list[str] = []

        def publish_heartbeat() -> None:
            sequence, previous = 0, None
            while not stop_heartbeat.is_set():
                values = dict(
                    schema_version="aidp-execution-heartbeat-v1", execution_id=request.execution_id,
                    sequence=sequence, observed_at=utc_now(), state=ExecutionStatus.RUNNING,
                    previous_digest=previous,
                )
                heartbeat = ExecutionHeartbeatV1(heartbeat_digest=canonical_digest(values), **values)
                try:
                    self.runtime_store.persist_execution_heartbeat(heartbeat)
                except Exception as exc:
                    heartbeat_failure.append(exc.__class__.__name__)
                    supervision_failure.set()
                    return
                previous, sequence = heartbeat.heartbeat_digest, sequence + 1
                stop_heartbeat.wait(5.0)

        thread = threading.Thread(target=publish_heartbeat, daemon=True)
        thread.start()
        try:
            result = self.execution_service.execute(request, supervision_event=supervision_failure)
        except Exception as exc:
            result = self._unexpected_result(request, request.expected_head, f"unexpected executor failure: {exc.__class__.__name__}")
        finally:
            stop_heartbeat.set(); thread.join(timeout=6.0)
        if heartbeat_failure:
            result = replace(
                result, status=ExecutionStatus.SUPERVISION_FAILED,
                failure_reason=f"execution heartbeat persistence failed: {heartbeat_failure[0]}",
            )
        self.runtime_store.persist_result(result)
        return result

    def run_ready(self, contract_id: str | None = None, *, attempt_ordinal: int = 0, retry_budget: int = 1) -> RunnerResult:
        if contract_id is None and self._contract_context is not None:
            contract_id, attempt_ordinal, retry_budget, recovery_scope = self._contract_context
        else:
            recovery_scope = None
        self._contract_context = None
        try:
            decision = self.repository.inspect()
        except (OSError, RuntimeError) as exc:
            return RunnerResult(
                RunnerStatus.ERROR,
                None,
                AIDPState.BLOCKED,
                None,
                f"repository inspection failed: {exc.__class__.__name__}",
            )

        executable = decision.state is AIDPState.READY_FOR_CODEX or (
            decision.state is AIDPState.REWORK_REQUIRED
            and decision.next_state is AIDPState.READY_FOR_CODEX
        )
        if not executable:
            status = RunnerStatus.BLOCKED if decision.state in {AIDPState.BLOCKED, AIDPState.STALE_EXECUTION} else RunnerStatus.NO_ACTION
            result = RunnerResult(
                status,
                decision.task_id,
                decision.state,
                decision.next_state,
                "; ".join(decision.reasons) or f"state {decision.state} is not executable",
            )
            self._audit(decision.state, decision.state, decision.next_state, result.decision_reason, decision, None)
            return result

        request: CodexExecutionRequest | None = None
        try:
            if decision.task_id is None:
                raise ValueError("executable inspection has no task")
            rework_count = 1 if decision.state is AIDPState.REWORK_REQUIRED else 0
            request = self.repository.build_execution_request(decision.task_id, rework_count=rework_count)
            if recovery_scope is not None:
                request = replace(request, allowed_scope=recovery_scope)
        except Exception as exc:
            reason = f"runner failed closed: {exc.__class__.__name__}"
            self._audit_safely(decision.state, decision.state, None, reason, decision, None)
            return RunnerResult(RunnerStatus.ERROR, decision.task_id, decision.state, None, reason)

        if contract_id is None:
            contract_id = canonical_digest({"task_id": request.task_id, "expected_head": request.expected_head, "scope": request.allowed_scope})
        attempt = ExecutionAttemptV1(
            "aidp-execution-attempt-v1", request.execution_id, contract_id, request.task_id,
            getattr(self.repository, "task_namespace", "product"), canonical_digest(str(self.repository.root.resolve()).lower()),
            request.expected_head, canonical_digest({"allowed": request.allowed_scope, "prohibited": request.prohibited_actions}),
            attempt_ordinal, retry_budget, utc_now(),
        )
        try:
            self.runtime_store.persist_execution_attempt(attempt)
        except Exception as exc:
            reason = f"execution attempt persistence failed: {exc.__class__.__name__}"
            return RunnerResult(RunnerStatus.ERROR, decision.task_id, decision.state, None, reason)
        stop_heartbeat = threading.Event()
        supervision_failure = threading.Event()
        heartbeat_failure: list[str] = []
        def publish_heartbeat() -> None:
            sequence, previous = 0, None
            while not stop_heartbeat.is_set():
                values = dict(schema_version="aidp-execution-heartbeat-v1", execution_id=request.execution_id,
                              sequence=sequence, observed_at=utc_now(), state=ExecutionStatus.RUNNING,
                              previous_digest=previous)
                heartbeat = ExecutionHeartbeatV1(heartbeat_digest=canonical_digest(values), **values)
                try: self.runtime_store.persist_execution_heartbeat(heartbeat)
                except Exception as exc:
                    exception_class = exc.__class__.__name__
                    heartbeat_failure.append(exception_class)
                    values = dict(
                        schema_version="aidp-execution-supervision-failure-v1",
                        execution_id=request.execution_id,
                        exception_class=exception_class,
                        observed_at=utc_now(),
                    )
                    failure = ExecutionSupervisionFailureV1(
                        failure_id=canonical_digest(values), **values,
                    )
                    try:
                        self.runtime_store.persist_supervision_failure(failure)
                    except Exception:
                        pass
                    supervision_failure.set()
                    return
                previous, sequence = heartbeat.heartbeat_digest, sequence + 1
                stop_heartbeat.wait(5.0)
        heartbeat_thread = threading.Thread(target=publish_heartbeat, daemon=True)
        heartbeat_thread.start()
        shutdown_requested = False
        try:
            parameters = inspect.signature(self.execution_service.execute).parameters
            execution_result = (
                self.execution_service.execute(request, supervision_event=supervision_failure)
                if "supervision_event" in parameters
                else self.execution_service.execute(request)
            )
        except KeyboardInterrupt:
            shutdown_requested = True
            execution_result = self._unexpected_result(request, decision.commit, "execution interrupted: KeyboardInterrupt")
        except Exception as exc:
            execution_result = self._unexpected_result(request, decision.commit, f"unexpected executor failure: {exc.__class__.__name__}")
        finally:
            stop_heartbeat.set(); heartbeat_thread.join(timeout=6.0)
        if heartbeat_failure:
            execution_result = replace(
                execution_result,
                status=ExecutionStatus.SUPERVISION_FAILED,
                failure_reason=f"execution heartbeat persistence failed: {heartbeat_failure[0]}",
            )

        try:
            self.runtime_store.persist_result(execution_result)
        except Exception as exc:
            reason = f"execution result persistence failed: {exc.__class__.__name__}"
            self._audit_safely(decision.state, decision.state, None, reason, decision, request.execution_id)
            return RunnerResult(
                RunnerStatus.ERROR, decision.task_id, decision.state, None,
                reason, execution_result, shutdown_requested,
            )

        try:
            intended_next = self.repository.evaluate_result(request, execution_result)
        except Exception:
            intended_next = None
        reason = f"execution completed with status {execution_result.status}"
        audited = self._audit_safely(
            decision.state, decision.state, intended_next, reason, decision, request.execution_id,
        )
        if not audited:
            reason = "execution result persisted but audit persistence failed"
            return RunnerResult(
                RunnerStatus.ERROR, decision.task_id, decision.state, intended_next,
                reason, execution_result, shutdown_requested,
            )
        return RunnerResult(
            RunnerStatus.EXECUTED, decision.task_id, decision.state, intended_next,
            reason, execution_result, shutdown_requested,
        )

    def _audit(
        self,
        previous: AIDPState,
        current: AIDPState,
        intended: AIDPState | None,
        reason: str,
        decision: OrchestrationDecision,
        execution_id: str | None,
    ) -> None:
        self.runtime_store.append_audit(
            AuditEvent(
                utc_now(),
                decision.task_id,
                previous,
                current,
                intended,
                "run-ready",
                decision.branch,
                decision.commit,
                execution_id,
                reason,
            )
        )

    def _audit_safely(
        self,
        previous: AIDPState,
        current: AIDPState,
        intended: AIDPState | None,
        reason: str,
        decision: OrchestrationDecision,
        execution_id: str | None,
    ) -> bool:
        try:
            self._audit(previous, current, intended, reason, decision, execution_id)
        except Exception:
            return False
        return True

    @staticmethod
    def _unexpected_result(
        request: CodexExecutionRequest,
        start_commit: str,
        reason: str,
    ) -> CodexExecutionResult:
        return CodexExecutionResult(
            request.execution_id,
            request.task_id,
            start_commit,
            None,
            (),
            (),
            ExecutionStatus.ERROR,
            reason,
            ScopeCompliance.NOT_EVALUATED,
        )


def serialize_runner_result(result: RunnerResult) -> str:
    """Stable JSON without prompts, process output, or secrets."""
    return json.dumps({"runner_result": asdict(result)}, default=_json_default, sort_keys=True)


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"unsupported serialization type: {type(value).__name__}")
