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
from typing import Callable, Protocol

from .contracts import (
    ArchitectIngressResult, IngressStatus, LifecycleResult, LifecycleStatus, TriggerResult, TriggerStatus, WatchIterationEvent, WatchRuntimeResult,
    WatchRuntimeStatus, ExternalWatcherHealth, ExternalWatcherOutcome,
    WatcherHeartbeatV1, canonical_digest, utc_now,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import AIDPWatchOnce


MINIMUM_WATCH_INTERVAL_SECONDS = 5.0
DEFAULT_WATCH_INTERVAL_SECONDS = 10.0


class WatchOnceBoundary(Protocol):
    def run_once(self) -> TriggerResult: ...


class IngressBoundary(Protocol):
    def run_once(self) -> ArchitectIngressResult: ...


class LifecycleBoundary(Protocol):
    def run_once(self) -> LifecycleResult: ...


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
                    self.event_sink(serialize_watch_iteration_event(event))
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
