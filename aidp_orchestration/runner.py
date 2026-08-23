"""Explicit, fail-closed trigger boundary for one ready AIDP execution."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
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
    utc_now,
)
from .executor import CodexExecutionService
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore


class ExecutionService(Protocol):
    def execute(self, request: CodexExecutionRequest) -> CodexExecutionResult: ...


class RuntimeStore(Protocol):
    def persist_result(self, result: CodexExecutionResult) -> Path: ...

    def append_audit(self, event: AuditEvent) -> Path: ...


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
    ):
        self.repository = repository
        self.execution_service = execution_service or CodexExecutionService(
            repository_root=repository.root,
            timeout_seconds=timeout_seconds,
        )
        self.runtime_store = runtime_store or LocalRuntimeStore.for_repository(repository.root)

    def run_ready(self) -> RunnerResult:
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

        try:
            if decision.task_id is None:
                raise ValueError("executable inspection has no task")
            rework_count = 1 if decision.state is AIDPState.REWORK_REQUIRED else 0
            request = self.repository.build_execution_request(decision.task_id, rework_count=rework_count)
            execution_result = self.execution_service.execute(request)
            self.runtime_store.persist_result(execution_result)
            intended_next = self.repository.evaluate_result(request, execution_result)
            reason = f"execution completed with status {execution_result.status}"
            self._audit(decision.state, decision.state, intended_next, reason, decision, request.execution_id)
            return RunnerResult(
                RunnerStatus.EXECUTED,
                decision.task_id,
                decision.state,
                intended_next,
                reason,
                execution_result,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            reason = f"runner failed closed: {exc.__class__.__name__}"
            self._audit(decision.state, decision.state, None, reason, decision, None)
            return RunnerResult(RunnerStatus.ERROR, decision.task_id, decision.state, None, reason)

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
