"""Local, single-process runtime shell around ``AIDPWatchOnce.run_once``."""

from __future__ import annotations

import json
import math
import os
import time
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from .contracts import (
    ArchitectIngressResult, IngressStatus, TriggerResult, TriggerStatus, WatchIterationEvent, WatchRuntimeResult,
    WatchRuntimeStatus, utc_now,
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


class WatcherRuntimeLock:
    """Atomic local lock; it provides no global or distributed exclusivity."""

    def __init__(self, path: Path):
        self.path = path
        self._owned = False

    @classmethod
    def for_repository(cls, repository_root: Path) -> "WatcherRuntimeLock":
        return cls(LocalRuntimeStore.for_repository(repository_root).root / "watcher-runtime.lock")

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        try:
            os.write(descriptor, f"pid={os.getpid()}\n".encode("ascii"))
        finally:
            os.close(descriptor)
        self._owned = True
        return True

    def release(self) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False


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

    def run(self) -> WatchRuntimeResult:
        try:
            acquired = self.lock.acquire()
        except KeyboardInterrupt:
            return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, 0)
        except OSError as exc:
            return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, 0, f"watcher lock failed: {exc.__class__.__name__}")
        if not acquired:
            return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, 0, "another local watcher runtime is active")
        iteration = 0
        try:
            while True:
                iteration += 1
                ingress_result: ArchitectIngressResult | None = None
                if self.ingress is not None:
                    try:
                        ingress_result = self.ingress.run_once()
                    except KeyboardInterrupt:
                        return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, iteration - 1)
                    except Exception as exc:
                        ingress_result = ArchitectIngressResult(
                            IngressStatus.ERROR, None, None, None,
                            failure_reason=f"ingress iteration failed: {exc.__class__.__name__}",
                        )
                try:
                    trigger_result = self.watcher.run_once()
                except KeyboardInterrupt:
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
                )
                try:
                    self.event_sink(serialize_watch_iteration_event(event))
                except Exception as exc:
                    return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, iteration, f"watch event sink failed: {exc.__class__.__name__}")
                try:
                    self.sleeper(self.interval_seconds)
                except KeyboardInterrupt:
                    return WatchRuntimeResult(WatchRuntimeStatus.STOPPED, iteration)
                except Exception as exc:
                    return WatchRuntimeResult(WatchRuntimeStatus.BLOCKED, iteration, f"watch interval failed: {exc.__class__.__name__}")
        finally:
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
