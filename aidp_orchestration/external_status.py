"""Pure, allowlist-only composition of the external AIDP status snapshot."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
import unicodedata

from .contracts import (
    ExternalConsistency, ExternalNextTask, ExternalStatusProjectionV1,
    ExternalWatcherHealth, ExternalWatcherOutcome, WatcherHeartbeatV1,
    canonical_digest, utc_now,
)


@dataclass(frozen=True, slots=True)
class RepositoryStatusObservation:
    head: str
    task_id: str | None
    lifecycle_state: str
    task_phase: str | None
    task_status: str
    product_owner_gate: str
    next_task: ExternalNextTask
    observed_at: datetime
    issues: tuple[str, ...] = ()

    def __post_init__(self):
        if self.task_phase not in {None,"implementation","acceptance","rework","UNKNOWN"}: raise ValueError("invalid repository phase")
        if len(self.issues)>16 or any(not x.isupper() or len(x)>64 for x in self.issues): raise ValueError("invalid repository issue")


@dataclass(frozen=True, slots=True)
class RuntimeStatusObservation:
    architect_status: str = "UNKNOWN"
    execution_status: str = "UNKNOWN"
    validation_summary: str = "UNKNOWN"
    blocker_code: str | None = None
    blocker_category: str = "NONE"
    blocker_message: str | None = None
    human_action_required: bool = False
    human_action_kind: str = "NONE"
    observed_at: datetime | None = None
    issues: tuple[str, ...] = ()

    def __post_init__(self):
        for value in (self.blocker_code,self.blocker_category,self.human_action_kind,*self.issues):
            if value is not None and (len(value)>64 or not value.replace("_","").isalnum()): raise ValueError("invalid runtime status code")
        if self.blocker_message is not None and (len(self.blocker_message)>160 or any(unicodedata.category(c) in {"Cc","Cf"} for c in self.blocker_message)): raise ValueError("invalid runtime message")


class RepositoryStatusReader(Protocol):
    def observe(self) -> RepositoryStatusObservation: ...


class RuntimeStatusReader(Protocol):
    def observe(self, repository: RepositoryStatusObservation) -> RuntimeStatusObservation: ...


class WatcherStatusReader(Protocol):
    def latest_heartbeat(self) -> WatcherHeartbeatV1 | None: ...


class ExternalStatusSnapshotWriter(Protocol):
    def persist_external_status(self, projection: ExternalStatusProjectionV1): ...


class ExternalStatusProjector:
    """Never executes orchestration; it only composes bounded observations."""
    def __init__(self, repository: RepositoryStatusReader, runtime: RuntimeStatusReader,
                 watcher: WatcherStatusReader, writer: ExternalStatusSnapshotWriter, *, clock=utc_now):
        self.repository, self.runtime, self.watcher, self.writer, self.clock = repository, runtime, watcher, writer, clock

    def project(self) -> ExternalStatusProjectionV1:
        now = self.clock()
        try:
            first = self.repository.observe()
            runtime = self.runtime.observe(first)
            heartbeat = self.watcher.latest_heartbeat()
            second = self.repository.observe()
        except (OSError, RuntimeError, TypeError, ValueError):
            projection = self._unavailable(now)
            self.writer.persist_external_status(projection)
            return projection
        issues = list(dict.fromkeys((*first.issues, *runtime.issues)))
        consistency = ExternalConsistency.CONSISTENT
        first_binding = (first.head, first.task_id, first.lifecycle_state, first.task_phase, first.task_status, first.product_owner_gate, first.next_task, first.issues)
        second_binding = (second.head, second.task_id, second.lifecycle_state, second.task_phase, second.task_status, second.product_owner_gate, second.next_task, second.issues)
        if first_binding != second_binding:
            issues.append("HEAD_CHANGED_DURING_PROJECTION" if first.head != second.head else "LIFECYCLE_CHANGED_DURING_PROJECTION")
            consistency = ExternalConsistency.CONFLICT
        elif issues:
            consistency = ExternalConsistency.CONFLICT if "MULTIPLE_ACTIVE_TASKS" in issues else ExternalConsistency.STALE
        watcher_status, age, outcome, activity = self._watcher(heartbeat, now)
        if watcher_status is ExternalWatcherHealth.STALE:
            issues.append("WATCHER_HEARTBEAT_STALE")
            if consistency is ExternalConsistency.CONSISTENT: consistency = ExternalConsistency.STALE
        values = dict(
            schema_version="aidp-external-status-v1", generated_at=now,
            repository_id="predatorai-product", product_head=second.head if first.head == second.head else None,
            head_status="CURRENT" if first.head == second.head else "CHANGED_DURING_READ",
            task_id=second.task_id if consistency is not ExternalConsistency.CONFLICT else None,
            task_phase=second.task_phase if consistency is not ExternalConsistency.CONFLICT else None,
            task_status=second.task_status if consistency is not ExternalConsistency.CONFLICT else "UNKNOWN",
            lifecycle_state=second.lifecycle_state if consistency is not ExternalConsistency.CONFLICT else "UNKNOWN",
            product_owner_gate=second.product_owner_gate if consistency is not ExternalConsistency.CONFLICT else "UNKNOWN",
            architect_status=runtime.architect_status, execution_status=runtime.execution_status,
            validation_summary=runtime.validation_summary, watcher_status=watcher_status,
            watcher_last_activity_at=activity, watcher_activity_age_seconds=age, watcher_last_outcome=outcome,
            blocker_code=runtime.blocker_code, blocker_category=runtime.blocker_category,
            blocker_message=runtime.blocker_message, human_action_required=runtime.human_action_required,
            human_action_kind=runtime.human_action_kind, next_task=second.next_task,
            consistency=consistency, consistency_issues=tuple(dict.fromkeys(issues)),
            oldest_observation_at=min(x for x in (first.observed_at, runtime.observed_at, activity) if x is not None),
        )
        identity = canonical_digest(values)
        projection = ExternalStatusProjectionV1(projection_id=identity, **values)
        self.writer.persist_external_status(projection)
        return projection

    @staticmethod
    def _watcher(value, now):
        if value is None: return ExternalWatcherHealth.UNKNOWN, None, ExternalWatcherOutcome.UNKNOWN, None
        if value.observed_at > now + timedelta(seconds=60):
            return ExternalWatcherHealth.UNKNOWN, None, ExternalWatcherOutcome.UNKNOWN, value.observed_at
        age = max(0, int((now - value.observed_at).total_seconds()))
        limit = min(300, max(30, int(3 * value.expected_interval_seconds)))
        status = ExternalWatcherHealth.STALE if age > limit else value.status
        return status, age, value.last_outcome, value.observed_at

    @staticmethod
    def _unavailable(now):
        values = dict(schema_version="aidp-external-status-v1", generated_at=now, repository_id="predatorai-product",
            product_head=None, head_status="UNAVAILABLE", task_id=None, task_phase=None, task_status="UNKNOWN",
            lifecycle_state="UNKNOWN", product_owner_gate="UNKNOWN", architect_status="UNKNOWN",
            execution_status="UNKNOWN", validation_summary="UNKNOWN", watcher_status=ExternalWatcherHealth.UNKNOWN,
            watcher_last_activity_at=None, watcher_activity_age_seconds=None, watcher_last_outcome=ExternalWatcherOutcome.UNKNOWN,
            blocker_code="AUTHORITATIVE_SOURCE_UNAVAILABLE", blocker_category="DEPENDENCY",
            blocker_message="Authoritative status is unavailable.", human_action_required=False, human_action_kind="NONE",
            next_task=ExternalNextTask.UNKNOWN, consistency=ExternalConsistency.UNAVAILABLE,
            consistency_issues=("AUTHORITATIVE_SOURCE_UNAVAILABLE",), oldest_observation_at=None)
        return ExternalStatusProjectionV1(projection_id=canonical_digest(values), **values)
