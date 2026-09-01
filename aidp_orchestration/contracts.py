"""Immutable contracts used by the AIDP orchestration boundary."""

from __future__ import annotations

import re
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, StrEnum
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


class IngressStatus(StrEnum):
    NO_ACTION = "NO_ACTION"
    MATERIALIZED = "MATERIALIZED"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"


class ArchitectReviewDisposition(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


class LifecycleStatus(StrEnum):
    NO_ACTION = "NO_ACTION"
    ADVANCED = "ADVANCED"
    BLOCKED = "BLOCKED"
    ESCALATION_REQUIRED = "ESCALATION_REQUIRED"


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
    shutdown_requested: bool = False


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
        validate_task_id(self.task_id)
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
class ArchitectFinding:
    finding_id: str
    rule_id: str
    severity: str
    summary: str
    evidence_paths: tuple[str, ...]
    action_id: str
    required_change: str

    def __post_init__(self) -> None:
        for name in ("finding_id", "rule_id", "severity", "summary", "action_id", "required_change"):
            _single_line(getattr(self, name), name)
        if not self.evidence_paths or any(not value.strip() for value in self.evidence_paths):
            raise ValueError("evidence_paths must contain explicit values")
        if tuple(sorted(set(self.evidence_paths))) != self.evidence_paths:
            raise ValueError("evidence_paths must be unique and sorted")

    @property
    def fingerprint(self) -> str:
        return _digest({
            "schema": "architect-finding-v1",
            "rule_id": self.rule_id,
            "severity": self.severity,
            "evidence_paths": self.evidence_paths,
            "action_id": self.action_id,
        })


@dataclass(frozen=True, slots=True)
class ArchitectReviewRequest:
    review_request_id: str
    task_id: str
    review_iteration: int
    execution_id: str
    repository: str
    git_common_dir: str
    branch: str
    remote_url: str
    authority_contract_id: str
    authority_contract_digest: str
    original_allowed_scope: tuple[str, ...]
    original_prohibited_actions: tuple[str, ...]
    original_validation_requirements: tuple[str, ...]
    original_acceptance_criteria: tuple[str, ...]
    product_owner_gate: bool
    review_envelope_path: str
    review_envelope_digest: str
    execution_status: ExecutionStatus
    start_commit: str
    resulting_commit: str
    review_envelope_commit: str
    changed_files: tuple[str, ...]
    validation_results: tuple[ValidationResult, ...]
    scope_compliance: ScopeCompliance
    expected_current_head: str
    current_head: str
    reviewed_head: str
    reviewed_tree_hash: str
    previous_review_result_id: str | None
    previous_rework_contract_id: str | None
    previous_finding_fingerprints: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "review_request_id", "task_id", "execution_id", "repository", "git_common_dir", "branch",
            "remote_url", "authority_contract_id", "authority_contract_digest", "review_envelope_path",
            "review_envelope_digest", "start_commit", "resulting_commit", "review_envelope_commit",
            "expected_current_head", "current_head", "reviewed_head", "reviewed_tree_hash",
        ):
            _single_line(getattr(self, name), name)
        if self.review_iteration < 0 or self.review_iteration > 3:
            raise ValueError("review_iteration must be between 0 and 3")
        validate_task_id(self.task_id)
        for name in ("review_request_id", "authority_contract_digest", "review_envelope_digest"):
            _sha256(getattr(self, name), name)
        for name in ("start_commit", "resulting_commit", "review_envelope_commit", "expected_current_head", "current_head", "reviewed_head", "reviewed_tree_hash"):
            _git_identity(getattr(self, name), name)
        if not self.original_allowed_scope or not self.original_validation_requirements or not self.original_acceptance_criteria:
            raise ValueError("original task authority must be explicit")
        for name in ("original_allowed_scope", "original_validation_requirements", "changed_files", "previous_finding_fingerprints"):
            values = getattr(self, name)
            if len(values) != len(set(values)):
                raise ValueError(f"{name} must not contain duplicates")
        if not self.changed_files or tuple(sorted(set(self.changed_files))) != self.changed_files:
            raise ValueError("changed_files must be unique, sorted and non-empty")
        if not self.validation_results or any(not result.passed for result in self.validation_results):
            raise ValueError("review request requires passing validator evidence")
        if self.execution_status is not ExecutionStatus.SUCCESS or self.scope_compliance is not ScopeCompliance.COMPLIANT:
            raise ValueError("review request requires successful compliant execution")
        if self.current_head != self.expected_current_head or self.reviewed_head != self.resulting_commit:
            raise ValueError("review request HEAD binding is inconsistent")
        if not self.product_owner_gate:
            raise ValueError("autonomous Architect review requires an explicit Product Owner gate")
        _aware(self.created_at, "created_at")
        if self.review_request_id != self.expected_id():
            raise ValueError("review_request_id is not deterministic")

    def expected_id(self) -> str:
        return _digest({
            "schema": "architect-review-request-v1",
            "task_id": self.task_id,
            "review_iteration": self.review_iteration,
            "execution_id": self.execution_id,
            "authority_contract_digest": self.authority_contract_digest,
            "review_envelope_digest": self.review_envelope_digest,
            "expected_current_head": self.expected_current_head,
            "reviewed_head": self.reviewed_head,
            "reviewed_tree_hash": self.reviewed_tree_hash,
        })


@dataclass(frozen=True, slots=True)
class ArchitectReviewProvenance:
    process_identity: str
    launcher_identity: str
    model: str
    invocation_started_at: datetime
    invocation_completed_at: datetime
    output_schema_version: str

    def __post_init__(self) -> None:
        for name in ("process_identity", "launcher_identity", "model", "output_schema_version"):
            _single_line(getattr(self, name), name)
        _aware(self.invocation_started_at, "invocation_started_at")
        _aware(self.invocation_completed_at, "invocation_completed_at")
        if self.invocation_completed_at < self.invocation_started_at:
            raise ValueError("Architect invocation completion precedes start")


@dataclass(frozen=True, slots=True)
class ArchitectReviewResult:
    review_result_id: str
    review_request_id: str
    task_id: str
    execution_id: str
    review_iteration: int
    disposition: ArchitectReviewDisposition
    reviewed_head: str
    expected_head: str
    reviewed_tree_hash: str
    findings: tuple[ArchitectFinding, ...]
    allowed_rework_scope: tuple[str, ...]
    required_validations: tuple[str, ...]
    provenance: ArchitectReviewProvenance
    failure_reason: str | None
    authority_claims: tuple[str, ...]
    created_at: datetime

    def __post_init__(self) -> None:
        for name in ("review_result_id", "review_request_id", "task_id", "execution_id", "reviewed_head", "expected_head", "reviewed_tree_hash"):
            _single_line(getattr(self, name), name)
        if self.review_iteration < 0 or self.review_iteration > 3:
            raise ValueError("review_iteration must be between 0 and 3")
        validate_task_id(self.task_id)
        _sha256(self.review_result_id, "review_result_id")
        _sha256(self.review_request_id, "review_request_id")
        for name in ("reviewed_head", "expected_head", "reviewed_tree_hash"):
            _git_identity(getattr(self, name), name)
        if self.failure_reason is not None and (len(self.failure_reason) > 2048 or "\n" in self.failure_reason or "\r" in self.failure_reason):
            raise ValueError("failure_reason must be a bounded single-line diagnostic")
        if self.authority_claims:
            raise ValueError("Architect result may not assert Product Owner, DONE or next-task authority")
        if self.disposition is ArchitectReviewDisposition.PASS:
            if self.findings or self.allowed_rework_scope or self.required_validations or self.failure_reason:
                raise ValueError("PASS may not contain remediation or rework authority")
        elif self.disposition is ArchitectReviewDisposition.FAIL:
            if not self.findings or not self.allowed_rework_scope or not self.required_validations or self.failure_reason:
                raise ValueError("FAIL requires findings and explicit rework authority")
        else:
            if self.allowed_rework_scope or self.required_validations:
                raise ValueError("BLOCKED may not contain rework authority")
            if not self.failure_reason:
                raise ValueError("BLOCKED requires a failure reason")
        fingerprints = tuple(finding.fingerprint for finding in self.findings)
        if len(fingerprints) != len(set(fingerprints)):
            raise ValueError("duplicate canonical Architect finding")
        _aware(self.created_at, "created_at")
        if self.review_result_id != self.expected_id():
            raise ValueError("review_result_id is not deterministic")

    def expected_id(self) -> str:
        return _digest({
            "schema": "architect-review-result-v1",
            "review_request_id": self.review_request_id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "review_iteration": self.review_iteration,
            "disposition": self.disposition,
            "reviewed_head": self.reviewed_head,
            "expected_head": self.expected_head,
            "reviewed_tree_hash": self.reviewed_tree_hash,
            "findings": self.findings,
            "allowed_rework_scope": self.allowed_rework_scope,
            "required_validations": self.required_validations,
            "provenance": self.provenance,
            "failure_reason": self.failure_reason,
            "authority_claims": self.authority_claims,
            "created_at": self.created_at,
        })


@dataclass(frozen=True, slots=True)
class LifecycleResult:
    status: LifecycleStatus
    task_id: str | None
    state: AIDPState
    reason: str
    execution_id: str | None = None
    review_request_id: str | None = None
    review_result_id: str | None = None


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
        validate_task_id(self.task_id)
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
    ingress_status: IngressStatus | None = None
    remote_contract_id: str | None = None
    remote_contract_commit: str | None = None
    ingress_failure_reason: str | None = None
    lifecycle_status: LifecycleStatus | None = None


@dataclass(frozen=True, slots=True)
class WatchRuntimeResult:
    status: WatchRuntimeStatus
    iterations: int
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ArchitectIngressResult:
    status: IngressStatus
    contract_id: str | None
    remote_commit: str | None
    blob_id: str | None
    local_inbox_path: str | None = None
    failure_reason: str | None = None


@dataclass(frozen=True, slots=True)
class ArchitectIngressAcceptanceResult:
    status: AcceptanceStatus
    remote_contract_branch: str
    remote_contract_commit: str | None
    contract_id: str
    ingress_status: IngressStatus
    local_inbox_materialized: bool
    local_contract_verified: bool
    second_ingress_status: IngressStatus | None
    mutation_guard_verified: bool
    source_aidp_unchanged: bool
    cleanup_status: CleanupStatus
    temporary_repository: str
    temporary_remote: str
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


def canonical_digest(value: object) -> str:
    if isinstance(value, bytes):
        return hashlib.sha256(value).hexdigest()
    return _digest(value)


def _digest(value: object) -> str:
    encoded = json.dumps(value, default=_canonical_default, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_default(value: object) -> object:
    if hasattr(value, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    raise TypeError(type(value).__name__)


def _single_line(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value:
        raise ValueError(f"{name} must be an explicit single-line value")


def _aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


def _sha256(value: str, name: str) -> None:
    if re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 identity")


def _git_identity(value: str, name: str) -> None:
    if re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", value) is None:
        raise ValueError(f"{name} must be an exact Git object identity")


def validate_task_id(value: str) -> None:
    if re.fullmatch(r"(?:TASK-(?:\d{4}|E2E-(?:(?:WRITER|TRIGGER)-)?\d{4})|AIDP-INFRA-\d{4})", value) is None:
        raise ValueError("task_id is not authorized")
