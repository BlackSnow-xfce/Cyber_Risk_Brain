"""Local, single-process runtime shell around ``AIDPWatchOnce.run_once``."""

from __future__ import annotations

import json
import math
import os
import platform
import secrets
import time
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Protocol

from .contracts import (
    AIDPState, ArchitectIngressResult, IngressStatus, LifecycleResult, LifecycleStatus, TriggerResult, TriggerStatus, WatchIterationEvent, WatchRuntimeResult,
    WatchRuntimeStatus, ExternalWatcherHealth, ExternalWatcherOutcome,
    WatcherHeartbeatV1, canonical_digest, utc_now,
    ProductOwnerGateDependencyResult, ProductOwnerGateDependencyState,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import AIDPWatchOnce
from .operator_stream import emit_activity


MINIMUM_WATCH_INTERVAL_SECONDS = 5.0
DEFAULT_WATCH_INTERVAL_SECONDS = 10.0


class WatchOnceBoundary(Protocol):
    def run_once(self) -> TriggerResult: ...


class IngressBoundary(Protocol):
    def run_once(self) -> ArchitectIngressResult: ...


class LifecycleBoundary(Protocol):
    def run_once(self) -> LifecycleResult: ...


class GateDependencyBoundary(Protocol):
    def run_once(self) -> ProductOwnerGateDependencyResult: ...


class SanitizedWatcherHeartbeatPublisher:
    def __init__(self, store: LocalRuntimeStore, *, expected_interval_seconds: float, clock=utc_now):
        self.store, self.expected_interval_seconds, self.clock = store, expected_interval_seconds, clock
        self.previous = store.watcher_heartbeat()
        self.instance_id = self.previous.watcher_instance_id if self.previous else canonical_digest(secrets.token_bytes(32))
        self.started_at = self.previous.started_at if self.previous else self.clock()

    def publish(self, status: ExternalWatcherHealth, outcome: ExternalWatcherOutcome) -> None:
        sequence = 0 if self.previous is None else self.previous.sequence + 1
        values = dict(schema_version="aidp-watcher-heartbeat-v1", watcher_instance_id=self.instance_id,
            sequence=sequence, started_at=self.started_at, observed_at=self.clock(),
            expected_interval_seconds=self.expected_interval_seconds, status=status, last_outcome=outcome,
            previous_heartbeat_digest=None if self.previous is None else self.previous.heartbeat_digest)
        heartbeat = WatcherHeartbeatV1(heartbeat_digest=canonical_digest(values), **values)
        self.store.persist_watcher_heartbeat(heartbeat); self.previous = heartbeat


class PersistentWatcherStatusPublisher:
    """Atomically publishes one sanitized current-status view outside task authority."""

    def __init__(self, root: Path, *, clock: Callable[[], datetime] = utc_now):
        self.json_path = root / "watcher-current-status.json"
        self.text_path = root / "watcher-current-status.txt"
        self.clock = clock

    def publish(self, event: WatchIterationEvent) -> None:
        overall = self._overall(event)
        component = self._component(event, overall)
        next_action = self._next_action(event, overall)
        payload = {
            "schema_version": "aidp-watcher-current-status-v1",
            "updated_at": event.timestamp.isoformat(),
            "iteration": event.iteration,
            "overall_status": overall,
            "active_component": component,
            "last_activity": event.timestamp.isoformat(),
            "next_action": next_action,
            "trigger_status": event.trigger_status.value,
            "product": self._lane(
                event.product_task_id, event.product_state, event.product_lifecycle_status,
            ),
            "infrastructure": self._lane(
                event.infrastructure_task_id,
                event.infrastructure_state,
                event.infrastructure_lifecycle_status,
            ),
        }
        self._write_payload(payload)

    def publish_activity(self, encoded_event: str) -> None:
        """Project only bounded activity metadata; raw child output is never persisted."""

        try:
            envelope = json.loads(encoded_event)
            activity = envelope.get("operator_activity")
        except (json.JSONDecodeError, AttributeError):
            return
        if not isinstance(activity, dict):
            return
        source = activity.get("source")
        kind = activity.get("kind")
        if source not in {"AIDP", "CODEX", "ARCHITECT", "VALIDATION"} or not isinstance(kind, str):
            return
        payload = self._read_or_initial()
        timestamp = self.clock().isoformat()
        payload.update({
            "updated_at": timestamp,
            "overall_status": "WORKING",
            "active_component": source,
            "last_activity": timestamp,
            "activity_kind": kind[:64],
            "next_action": "CONTINUE_AUTOMATICALLY",
        })
        task_id = activity.get("task_id")
        if isinstance(task_id, str) and len(task_id) <= 64:
            lane_name = "infrastructure" if task_id.startswith("AIDP-INFRA-") else "product"
            lane = payload.get(lane_name)
            if isinstance(lane, dict):
                lane["task_id"] = task_id
        self._write_payload(payload)

    def _read_or_initial(self) -> dict[str, object]:
        try:
            value = json.loads(self.json_path.read_text(encoding="utf-8"))
            if isinstance(value, dict) and value.get("schema_version") == "aidp-watcher-current-status-v1":
                return value
        except (OSError, json.JSONDecodeError):
            pass
        return {
            "schema_version": "aidp-watcher-current-status-v1",
            "iteration": None,
            "trigger_status": None,
            "product": self._lane(None, None, None),
            "infrastructure": self._lane(None, None, None),
        }

    def _write_payload(self, payload: Mapping[str, object]) -> None:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
        text = (
            "AIDP WATCHER STATUS\n"
            f"Overall: {payload['overall_status']}\n"
            f"Updated: {payload['updated_at']}\n"
            f"Active component: {payload['active_component']}\n"
            f"Next action: {payload['next_action']}\n"
            f"Product: {self._lane_text(payload['product'])}\n"
            f"Infrastructure: {self._lane_text(payload['infrastructure'])}\n"
        )
        self._atomic_write(self.json_path, encoded)
        self._atomic_write(self.text_path, text)

    @staticmethod
    def _lane(
        task_id: str | None,
        state: AIDPState | None,
        status: LifecycleStatus | None,
    ) -> dict[str, str | None]:
        return {
            "task_id": task_id,
            "lifecycle_state": state.value if state is not None else None,
            "lifecycle_status": status.value if status is not None else None,
        }

    @staticmethod
    def _lane_text(lane: Mapping[str, str | None]) -> str:
        return f"{lane['task_id'] or 'NONE'} | {lane['lifecycle_state'] or 'UNKNOWN'} | {lane['lifecycle_status'] or 'UNKNOWN'}"

    @staticmethod
    def _overall(event: WatchIterationEvent) -> str:
        statuses = (event.product_lifecycle_status, event.infrastructure_lifecycle_status)
        if event.trigger_status in {TriggerStatus.BLOCKED, TriggerStatus.ERROR} or any(
            status in {LifecycleStatus.BLOCKED, LifecycleStatus.ESCALATION_REQUIRED}
            for status in statuses
        ):
            return "BLOCKED"
        states = tuple(state for state in (event.product_state, event.infrastructure_state) if state is not None)
        if states and all(state is AIDPState.DONE for state in states):
            return "DONE"
        if event.trigger_status is TriggerStatus.PUBLISHED or any(
            status is LifecycleStatus.ADVANCED for status in statuses
        ) or any(state is AIDPState.CODEX_RUNNING for state in states):
            return "WORKING"
        return "WAITING"

    @staticmethod
    def _component(event: WatchIterationEvent, overall: str) -> str:
        if event.contract_id is not None and event.contract_id not in {event.product_task_id, event.infrastructure_task_id}:
            return "PRODUCT_OWNER_GATE_DEPENDENCY"
        if event.infrastructure_lifecycle_status in {
            LifecycleStatus.ADVANCED, LifecycleStatus.BLOCKED, LifecycleStatus.ESCALATION_REQUIRED,
        }:
            return "INFRASTRUCTURE"
        if event.product_state is AIDPState.WAITING_FOR_PRODUCT_OWNER:
            return "PRODUCT_OWNER"
        if event.product_lifecycle_status in {
            LifecycleStatus.ADVANCED, LifecycleStatus.BLOCKED, LifecycleStatus.ESCALATION_REQUIRED,
        }:
            return "PRODUCT"
        return "NONE" if overall == "DONE" else "WATCHER"

    @staticmethod
    def _next_action(event: WatchIterationEvent, overall: str) -> str:
        if overall == "DONE":
            return "NONE"
        if overall == "BLOCKED":
            if LifecycleStatus.ESCALATION_REQUIRED in {
                event.product_lifecycle_status, event.infrastructure_lifecycle_status,
            }:
                return "HUMAN_ACTION_REQUIRED"
            return "OPERATOR_REVIEW"
        if overall == "WORKING":
            return "CONTINUE_AUTOMATICALLY"
        if event.product_state is AIDPState.WAITING_FOR_PRODUCT_OWNER:
            return "PRODUCT_OWNER_CONFIRMATION"
        if AIDPState.READY_FOR_ARCHITECT in {event.product_state, event.infrastructure_state}:
            return "ARCHITECT_REVIEW"
        if AIDPState.REWORK_REQUIRED in {event.product_state, event.infrastructure_state}:
            return "CODEX_REWORK"
        return "WAIT_FOR_AUTHORIZED_WORK"

    @staticmethod
    def _atomic_write(path: Path, value: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(value, encoding="utf-8", newline="\n")
        os.replace(temporary, path)


class WatcherRuntimeLock:
    """Atomic local lock; it provides no global or distributed exclusivity."""

    def __init__(self, path: Path, *, process_identity: Callable[[int], str | None] | None = None):
        self.path = path
        self._owned = False
        self._content: bytes | None = None
        self.process_identity = process_identity or _process_identity

    @classmethod
    def for_repository(cls, repository_root: Path) -> "WatcherRuntimeLock":
        return cls(LocalRuntimeStore.for_repository(repository_root).root / "watcher-runtime.lock")

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        identity = self.process_identity(os.getpid())
        if identity is None:
            raise RuntimeError("current watcher process identity is unavailable")
        content = json.dumps({"pid": os.getpid(), "process_identity": identity}, sort_keys=True).encode("utf-8") + b"\n"
        return self._acquire(content, allow_reclaim=True)

    def _acquire(self, content: bytes, *, allow_reclaim: bool) -> bool:
        try:
            descriptor = os.open(
                self.path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
            )
        except FileExistsError:
            if not allow_reclaim:
                return False
            return self._reclaim(content)
        try:
            os.write(descriptor, content)
        finally:
            os.close(descriptor)
        self._owned = True
        self._content = content
        return True

    def _reclaim(self, content: bytes) -> bool:
        guard = self.path.with_name(f"{self.path.name}.reclaim")
        try:
            descriptor = os.open(
                guard,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0),
            )
        except FileExistsError:
            return False
        os.close(descriptor)
        try:
            if not self.path.exists() or not self._existing_lock_is_stale():
                return False
            self.path.unlink()
            return self._acquire(content, allow_reclaim=False)
        finally:
            guard.unlink(missing_ok=True)

    def _existing_lock_is_stale(self) -> bool:
        content = self.path.read_bytes()
        pid, expected_identity = _parse_lock(content)
        observed_identity = self.process_identity(pid)
        if observed_identity is None:
            return True
        if expected_identity is None:
            return False
        return observed_identity != expected_identity

    def release(self) -> None:
        if self._owned:
            if self.path.exists() and self._content is not None and self.path.read_bytes() == self._content:
                self.path.unlink()
            self._owned = False
            self._content = None


class AIDPLocalWatcherRuntime:
    def __init__(
        self,
        repository: AIDPRepository,
        *,
        watcher: WatchOnceBoundary | None = None,
        interval_seconds: float = DEFAULT_WATCH_INTERVAL_SECONDS,
        lock: WatcherRuntimeLock | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        event_sink: Callable[[str], None] = print,
        clock: Callable[[], datetime] = utc_now,
        ingress: IngressBoundary | None = None,
        lifecycle: LifecycleBoundary | None = None,
        infrastructure_lifecycle: LifecycleBoundary | None = None,
        heartbeat: SanitizedWatcherHeartbeatPublisher | None = None,
        status_publisher: PersistentWatcherStatusPublisher | None = None,
        gate_dependency: GateDependencyBoundary | None = None,
    ):
        if not math.isfinite(interval_seconds) or interval_seconds < MINIMUM_WATCH_INTERVAL_SECONDS:
            raise ValueError(f"watch interval must be at least {MINIMUM_WATCH_INTERVAL_SECONDS:g} seconds")
        self.watcher = watcher or AIDPWatchOnce(repository)
        self.interval_seconds = interval_seconds
        self.lock = lock or WatcherRuntimeLock.for_repository(repository.root)
        self.sleeper = sleeper
        self.event_sink = event_sink
        self.clock = clock
        self.ingress = ingress
        self.lifecycle = lifecycle
        self.infrastructure_lifecycle = infrastructure_lifecycle
        self.heartbeat = heartbeat
        self.status_publisher = status_publisher
        self.gate_dependency = gate_dependency

    def run(self) -> WatchRuntimeResult:
        try:
            acquired = self.lock.acquire()
        except KeyboardInterrupt:
            return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, 0)
        except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
            return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, 0, f"watcher lock failed: {exc.__class__.__name__}")
        if not acquired:
            return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, 0, "another local watcher runtime is active")
        iteration = 0
        terminal_health = ExternalWatcherHealth.BLOCKED
        terminal_outcome = ExternalWatcherOutcome.BLOCKED
        try:
            if self.heartbeat is not None:
                try: self.heartbeat.publish(ExternalWatcherHealth.ACTIVE, ExternalWatcherOutcome.UNKNOWN)
                except Exception: return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, 0, "watcher heartbeat failed")
            while True:
                iteration += 1
                ingress_result: ArchitectIngressResult | None = None
                if self.ingress is not None:
                    try:
                        ingress_result = self.ingress.run_once()
                    except KeyboardInterrupt:
                        terminal_health, terminal_outcome = ExternalWatcherHealth.STOPPED, ExternalWatcherOutcome.STOPPED
                        return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, iteration - 1)
                    except Exception as exc:
                        ingress_result = ArchitectIngressResult(
                            IngressStatus.ERROR, None, None, None,
                            failure_reason=f"ingress iteration failed: {exc.__class__.__name__}",
                        )
                lifecycle_result: LifecycleResult | None = None
                infrastructure_result: LifecycleResult | None = None
                product_result: LifecycleResult | None = None
                try:
                    dependency_result = self.gate_dependency.run_once() if self.gate_dependency is not None else None
                    infrastructure_result = (
                        self.infrastructure_lifecycle.run_once()
                        if self.infrastructure_lifecycle is not None else None
                    )
                    if self.lifecycle is not None:
                        product_result = self.lifecycle.run_once()
                        lifecycle_result = (
                            infrastructure_result
                            if infrastructure_result is not None
                            and infrastructure_result.status is not LifecycleStatus.NO_ACTION
                            else product_result
                        )
                        trigger_result = _trigger_from_lifecycle(lifecycle_result)
                    elif infrastructure_result is not None:
                        lifecycle_result = infrastructure_result
                        trigger_result = _trigger_from_lifecycle(lifecycle_result)
                    else:
                        trigger_result = self.watcher.run_once()
                    if dependency_result is not None and dependency_result.state is not ProductOwnerGateDependencyState.NO_ACTION:
                        trigger_result = TriggerResult(
                            TriggerStatus.BLOCKED if dependency_result.state in {
                                ProductOwnerGateDependencyState.BLOCKED,
                                ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING,
                            } else TriggerStatus.PUBLISHED,
                            dependency_result.authority_id, None, failure_reason=dependency_result.reason,
                        )
                except KeyboardInterrupt:
                    terminal_health, terminal_outcome = ExternalWatcherHealth.STOPPED, ExternalWatcherOutcome.STOPPED
                    return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, iteration - 1)
                except Exception as exc:  # Runtime containment must not bypass the normal retry interval.
                    trigger_result = TriggerResult(
                        TriggerStatus.ERROR, None, None,
                        failure_reason=f"watch iteration failed: {exc.__class__.__name__}",
                    )
                event = WatchIterationEvent(
                    self.clock(), iteration, trigger_result.status, trigger_result.contract_id,
                    trigger_result.consumption_state, trigger_result.failure_reason,
                    ingress_result.status if ingress_result else None,
                    ingress_result.contract_id if ingress_result else None,
                    ingress_result.remote_commit if ingress_result else None,
                    ingress_result.failure_reason if ingress_result else None,
                    lifecycle_result.status if lifecycle_result else None,
                    product_result.status if product_result else None,
                    product_result.task_id if product_result else None,
                    product_result.state if product_result else None,
                    product_result.reason if product_result else None,
                    infrastructure_result.status if infrastructure_result else None,
                    infrastructure_result.task_id if infrastructure_result else None,
                    infrastructure_result.state if infrastructure_result else None,
                    infrastructure_result.reason if infrastructure_result else None,
                )
                try:
                    if self.status_publisher is not None:
                        self.status_publisher.publish(event)
                    self.event_sink(serialize_watch_iteration_event(event))
                    for lane, lifecycle_event in (
                        ("infrastructure", infrastructure_result), ("product", product_result),
                    ):
                        if lifecycle_event is not None:
                            emit_activity(
                                self.event_sink, "AIDP", "lifecycle_transition", lane=lane,
                                task_id=lifecycle_event.task_id, status=lifecycle_event.status.value,
                                state=lifecycle_event.state.value, reason=lifecycle_event.reason,
                            )
                except Exception as exc:
                    return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, iteration, f"watch event sink failed: {exc.__class__.__name__}")
                if self.heartbeat is not None:
                    outcome = ExternalWatcherOutcome.ADVANCED if trigger_result.status is TriggerStatus.PUBLISHED else ExternalWatcherOutcome.NO_ACTION if trigger_result.status is TriggerStatus.NO_ACTION else ExternalWatcherOutcome.ERROR
                    try: self.heartbeat.publish(ExternalWatcherHealth.ACTIVE, outcome)
                    except Exception: return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, iteration, "watcher heartbeat failed")
                try:
                    self.sleeper(self.interval_seconds)
                except KeyboardInterrupt:
                    terminal_health, terminal_outcome = ExternalWatcherHealth.STOPPED, ExternalWatcherOutcome.STOPPED
                    return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, iteration)
                except Exception as exc:
                    return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, iteration, f"watch interval failed: {exc.__class__.__name__}")
        finally:
            if self.heartbeat is not None:
                try: self.heartbeat.publish(terminal_health, terminal_outcome)
                except Exception: pass
            self.lock.release()


def serialize_watch_iteration_event(event: WatchIterationEvent) -> str:
    return json.dumps({"watch_iteration": asdict(event)}, default=_json_default, sort_keys=True, separators=(",", ":"))


def serialize_watch_runtime_result(result: WatchRuntimeResult) -> str:
    return json.dumps({"watch_runtime_result": asdict(result)}, default=_json_default, sort_keys=True, separators=(",", ":"))


def _json_default(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError(type(value).__name__)


def _parse_lock(content: bytes) -> tuple[int, str | None]:
    try:
        text = content.decode("utf-8", errors="strict").strip()
    except UnicodeError as exc:
        raise ValueError("watcher lock is not valid UTF-8") from exc
    if text.startswith("pid="):
        value = text.removeprefix("pid=")
        if not value.isdigit():
            raise ValueError("legacy watcher lock PID is invalid")
        pid = int(value)
        if pid <= 0:
            raise ValueError("legacy watcher lock PID is invalid")
        return pid, None
    value = json.loads(text)
    if not isinstance(value, dict) or set(value) != {"pid", "process_identity"}:
        raise ValueError("watcher lock schema is invalid")
    pid, identity = value["pid"], value["process_identity"]
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0 or not isinstance(identity, str) or not identity:
        raise ValueError("watcher lock identity is invalid")
    return pid, identity


def _trigger_from_lifecycle(result: LifecycleResult) -> TriggerResult:
    status = (
        TriggerStatus.NO_ACTION if result.status is LifecycleStatus.NO_ACTION
        else TriggerStatus.PUBLISHED if result.status is LifecycleStatus.ADVANCED
        else TriggerStatus.BLOCKED
    )
    return TriggerResult(status, None, None, failure_reason=None if status is TriggerStatus.PUBLISHED else result.reason)


def _process_identity(pid: int) -> str | None:
    if platform.system() == "Windows":
        return _windows_process_identity(pid)
    stat = Path(f"/proc/{pid}/stat")
    if stat.is_file():
        value = stat.read_text(encoding="utf-8")
        closing = value.rfind(")")
        if closing < 0:
            raise RuntimeError("process identity is unverifiable")
        fields = value[closing + 2:].split()
        if len(fields) < 20:
            raise RuntimeError("process identity is unverifiable")
        return fields[19]
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError as exc:
        raise RuntimeError("process identity is unverifiable") from exc
    return f"pid:{pid}"


def _windows_process_identity(pid: int) -> str | None:
    import ctypes
    from ctypes import wintypes

    process = ctypes.WinDLL("kernel32", use_last_error=True)
    process.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    process.OpenProcess.restype = wintypes.HANDLE
    process.GetProcessTimes.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
        ctypes.POINTER(wintypes.FILETIME), ctypes.POINTER(wintypes.FILETIME),
    )
    process.GetProcessTimes.restype = wintypes.BOOL
    process.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    process.GetExitCodeProcess.restype = wintypes.BOOL
    process.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = process.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:
            return None
        raise RuntimeError("process identity is unverifiable")
    try:
        creation, exit_time, kernel, user = (wintypes.FILETIME() for _ in range(4))
        exit_code = wintypes.DWORD()
        if not process.GetProcessTimes(handle, creation, exit_time, kernel, user):
            raise RuntimeError("process identity is unverifiable")
        if not process.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise RuntimeError("process identity is unverifiable")
        if exit_code.value != 259:
            return None
        created = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        return str(created)
    finally:
        process.CloseHandle(handle)
