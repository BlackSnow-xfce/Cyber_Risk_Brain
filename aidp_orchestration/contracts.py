"""Immutable contracts used by the AIDP orchestration boundary."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Sequence


class AIDPState(StrEnum):
    WAITING = "WAITING"
    READY_FOR_CODEX = "READY_FOR_CODEX"
    CODEX_RUNNING = "CODEX_RUNNING"
    READY_FOR_ARCHITECT = "READY_FOR_ARCHITECT"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    ARCHITECT_APPROVED = "ARCHITECT_APPROVED"
    WAITING_FOR_PRODUCT_OWNER = "WAITING_FOR_PRODUCT_OWNER"
    DONE = "DONE"
    BLOCKED = "BLOCKED"
    STALE_EXECUTION = "STALE_EXECUTION"


class ExecutionStatus(StrEnum):
    SUCCESS = "SUCCESS"
    TEST_FAILED = "TEST_FAILED"
    SCOPE_VIOLATION = "SCOPE_VIOLATION"
    BLOCKED = "BLOCKED"
    STALE_EXECUTION = "STALE_EXECUTION"
    ERROR = "ERROR"


class ScopeCompliance(StrEnum):
    COMPLIANT = "COMPLIANT"
    VIOLATION = "VIOLATION"
    NOT_EVALUATED = "NOT_EVALUATED"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True, slots=True)
class OrchestrationDecision:
    task_id: str | None
    state: AIDPState
    next_state: AIDPState | None
    branch: str
    commit: str
    reasons: tuple[str, ...]
    timestamp: datetime


@dataclass(frozen=True, slots=True)
class CodexExecutionRequest:
    task_id: str
    task_path: Path
    repository: str
    branch: str
    base_commit: str
    expected_head: str
    phase: str
    allowed_scope: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    created_at: datetime
    execution_id: str
    rework_count: int = 0

    def __post_init__(self) -> None:
        for name in ("task_id", "repository", "branch", "base_commit", "expected_head", "phase", "execution_id"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if not self.allowed_scope or not self.validation_requirements:
            raise ValueError("execution scope and validations must be explicit")
        if self.rework_count < 0:
            raise ValueError("rework_count must not be negative")


@dataclass(frozen=True, slots=True)
class CodexExecutionResult:
    execution_id: str
    task_id: str
    start_commit: str
    resulting_commit: str | None
    changed_files: tuple[str, ...]
    validation_results: tuple[ValidationResult, ...]
    status: ExecutionStatus
    failure_reason: str | None
    scope_compliance: ScopeCompliance

    def __post_init__(self) -> None:
        for name in ("execution_id", "task_id", "start_commit"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")

    @property
    def is_review_ready(self) -> bool:
        """SUCCESS means review-ready only; it never means approved."""

        return self.status is ExecutionStatus.SUCCESS and self.scope_compliance is ScopeCompliance.COMPLIANT


@dataclass(frozen=True, slots=True)
class AuditEvent:
    timestamp: datetime
    task_id: str | None
    previous_state: AIDPState
    next_state: AIDPState
    trigger: str
    branch: str
    commit: str
    execution_id: str | None
    decision_reason: str


@dataclass(frozen=True, slots=True)
class TaskMetadata:
    """Explicit front-matter metadata required before execution can start."""

    task_id: str
    phase: str
    allowed_scope: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    product_owner_gate: bool = False


@dataclass(frozen=True, slots=True)
class Handoff:
    status: str
    task_id: str | None
    task_status: str | None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_non_empty(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    cleaned = tuple(value.strip() for value in values if value.strip())
    if not cleaned:
        raise ValueError(f"{field_name} must contain at least one value")
    return cleaned
