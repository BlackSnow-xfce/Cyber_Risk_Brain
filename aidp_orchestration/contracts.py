"""Immutable contracts used by the AIDP orchestration boundary."""

from __future__ import annotations

import re
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


class RunnerStatus(StrEnum):
    NO_ACTION = "NO_ACTION"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class AcceptanceStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"


class CleanupStatus(StrEnum):
    CLEANED = "CLEANED"
    PRESERVED = "PRESERVED"
    FAILED = "FAILED"


class ControlPlaneAction(StrEnum):
    NO_ACTION = "NO_ACTION"
    BLOCKED = "BLOCKED"
    EXECUTE = "EXECUTE"
    READY_FOR_ARCHITECT = "READY_FOR_ARCHITECT"
    WAITING_FOR_PRODUCT_OWNER = "WAITING_FOR_PRODUCT_OWNER"


class WriterAction(StrEnum):
    BLOCKED = "BLOCKED"
    MATERIALIZE_READY = "MATERIALIZE_READY"
    MATERIALIZE_REWORK = "MATERIALIZE_REWORK"


class ConsumptionState(StrEnum):
    RECEIVED = "RECEIVED"
    MATERIALIZED = "MATERIALIZED"
    EXECUTING = "EXECUTING"
    REVIEW_PUBLISHED = "REVIEW_PUBLISHED"
    BLOCKED = "BLOCKED"


class TriggerStatus(StrEnum):
    NO_ACTION = "NO_ACTION"
    PUBLISHED = "PUBLISHED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class WatchRuntimeStatus(StrEnum):
    STOPPED = "STOPPED"
    BLOCKED = "BLOCKED"


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
    current_state: AIDPState
    intended_next_state: AIDPState | None
    trigger: str
    branch: str
    commit: str
    execution_id: str | None
    decision_reason: str


@dataclass(frozen=True, slots=True)
class RunnerResult:
    status: RunnerStatus
    task_id: str | None
    current_state: AIDPState
    intended_next_state: AIDPState | None
    decision_reason: str
    execution_result: CodexExecutionResult | None = None


@dataclass(frozen=True, slots=True)
class AcceptanceResult:
    status: AcceptanceStatus
    runner_result: RunnerResult | None
    result_persisted: bool
    audit_persisted: bool
    temporary_repository: str
    cleanup_status: CleanupStatus
    source_aidp_unchanged: bool
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ReworkContract:
    task_id: str
    review_iteration: int
    expected_head: str
    allowed_rework_scope: tuple[str, ...]
    findings: tuple[str, ...]
    required_validations: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("task_id", "expected_head"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")
        if self.review_iteration < 1:
            raise ValueError("review_iteration must be at least 1")
        for name in ("allowed_rework_scope", "findings", "required_validations"):
            values = getattr(self, name)
            if not values or any(not value.strip() for value in values):
                raise ValueError(f"{name} must contain explicit non-empty values")


@dataclass(frozen=True, slots=True)
class ControlPlaneDecision:
    action: ControlPlaneAction
    task_id: str | None
    repository_state: AIDPState
    branch: str
    commit: str
    reason: str


@dataclass(frozen=True, slots=True)
class ArchitectInboxEntry:
    task_id: str
    execution_id: str
    current_state: AIDPState
    intended_next_state: AIDPState | None
    execution_status: ExecutionStatus
    changed_files: tuple[str, ...]
    scope_compliance: ScopeCompliance
    validation_results: tuple[ValidationResult, ...]
    failure_reason: str | None
    branch: str
    start_commit: str
    resulting_commit: str | None
    timestamp: datetime

    def __post_init__(self) -> None:
        for name in ("task_id", "execution_id", "branch", "start_commit"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} must not be empty")


@dataclass(frozen=True, slots=True)
class ControlPlaneResult:
    decision: ControlPlaneDecision
    final_action: ControlPlaneAction
    runner_result: RunnerResult | None = None
    architect_inbox_entry: ArchitectInboxEntry | None = None
    architect_inbox_path: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ArchitectTaskContract:
    task_id: str
    title: str
    phase: str
    expected_head: str
    allowed_scope: tuple[str, ...]
    prohibited_actions: tuple[str, ...]
    validation_requirements: tuple[str, ...]
    acceptance_criteria: tuple[str, ...]
    product_owner_gate: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if re.fullmatch(r"TASK-(?:\d{4}|E2E-(?:WRITER|TRIGGER)-\d{4})", self.task_id) is None:
            raise ValueError("task_id must match an authorized task identifier")
        for name in ("title", "phase", "expected_head"):
            value = getattr(self, name)
            if not value.strip() or "\n" in value or "\r" in value:
                raise ValueError(f"{name} must be an explicit single-line value")
        for name in ("allowed_scope", "prohibited_actions", "validation_requirements", "acceptance_criteria"):
            values = getattr(self, name)
            if not values or any(not value.strip() or "\n" in value or "\r" in value for value in values):
                raise ValueError(f"{name} must contain explicit non-empty values")
        for name in ("allowed_scope", "prohibited_actions", "validation_requirements"):
            if any("," in value for value in getattr(self, name)):
                raise ValueError(f"{name} values must not contain commas")
        if not isinstance(self.product_owner_gate, bool):
            raise ValueError("product_owner_gate must be boolean")
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            raise ValueError("created_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class WriterDecision:
    action: WriterAction
    task_id: str | None
    branch: str
    commit: str
    reason: str


@dataclass(frozen=True, slots=True)
class WriterResult:
    decision: WriterDecision
    materialized_paths: tuple[str, ...] = ()
    rework_contract_path: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class WriterControlPlaneAcceptanceResult:
    status: AcceptanceStatus
    writer_result: WriterResult | None
    ready_commit: str | None
    control_plane_result: ControlPlaneResult | None
    changed_files: tuple[str, ...]
    scope_compliance: ScopeCompliance
    validation_results: tuple[ValidationResult, ...]
    architect_inbox_persisted: bool
    source_aidp_unchanged: bool
    cleanup_status: CleanupStatus
    temporary_repository: str
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ContractInboxItem:
    contract_id: str
    contract: ArchitectTaskContract | ReworkContract
    received_at: datetime

    def __post_init__(self) -> None:
        if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", self.contract_id) is None:
            raise ValueError("contract_id is invalid")
        if self.received_at.tzinfo is None or self.received_at.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class ConsumptionEvent:
    contract_id: str
    state: ConsumptionState
    timestamp: datetime
    reason: str


@dataclass(frozen=True, slots=True)
class ReviewEnvelope:
    task_id: str
    execution_id: str
    branch: str
    start_commit: str
    resulting_commit: str
    execution_status: ExecutionStatus
    changed_files: tuple[str, ...]
    scope_compliance: ScopeCompliance
    validation_results: tuple[ValidationResult, ...]
    failure_reason: str | None
    intended_next_state: AIDPState
    published_at: datetime


@dataclass(frozen=True, slots=True)
class PublishResult:
    branch: str
    execution_commit: str | None
    review_envelope_path: str | None
    review_envelope_commit: str | None
    push_status: str
    final_state: AIDPState | None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerResult:
    status: TriggerStatus
    contract_id: str | None
    consumption_state: ConsumptionState | None
    writer_result: WriterResult | None = None
    control_plane_result: ControlPlaneResult | None = None
    publish_result: PublishResult | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class TriggerPublisherAcceptanceResult:
    status: AcceptanceStatus
    first_trigger_result: TriggerResult | None
    second_trigger_result: TriggerResult | None
    execution_commit: str | None
    review_envelope_commit: str | None
    review_envelope_path: str | None
    remote_branch: str
    remote_head: str | None
    remote_envelope_verified: bool
    remote_probe_verified: bool
    idempotency_verified: bool
    source_aidp_unchanged: bool
    cleanup_status: CleanupStatus
    temporary_repository: str
    temporary_remote: str
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class WatchIterationEvent:
    timestamp: datetime
    iteration: int
    trigger_status: TriggerStatus
    contract_id: str | None
    consumption_state: ConsumptionState | None
    failure_reason: str | None


@dataclass(frozen=True, slots=True)
class WatchRuntimeResult:
    status: WatchRuntimeStatus
    iterations: int
    failure_reason: str | None = None


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
