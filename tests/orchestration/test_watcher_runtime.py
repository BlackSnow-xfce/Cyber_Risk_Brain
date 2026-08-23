from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    ConsumptionState, TriggerResult, TriggerStatus, WatchIterationEvent,
    WatchRuntimeResult, WatchRuntimeStatus,
)
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.trigger_publisher import AIDPWatchOnce
from aidp_orchestration.watcher_runtime import (
    AIDPLocalWatcherRuntime, WatcherRuntimeLock, serialize_watch_iteration_event,
    serialize_watch_runtime_result,
)


class SequenceWatcher:
    def __init__(self, results):
        self.results = iter(results)
        self.calls = 0

    def run_once(self):
        self.calls += 1
        value = next(self.results)
        if isinstance(value, BaseException):
            raise value
        return value


class StopAfter:
    def __init__(self, count: int):
        self.count = count
        self.calls = []

    def __call__(self, seconds: float):
        self.calls.append(seconds)
        if len(self.calls) >= self.count:
            raise KeyboardInterrupt


def _runtime(tmp_path: Path, watcher, sleeper, events=None, lock=None, interval=5.0):
    return AIDPLocalWatcherRuntime(
        AIDPRepository(tmp_path), watcher=watcher, sleeper=sleeper,
        event_sink=(events.append if events is not None else (lambda _: None)),
        lock=lock or WatcherRuntimeLock(tmp_path / "watch.lock"),
        interval_seconds=interval, clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_multiple_iterations_use_only_watch_once_and_observe_interval(tmp_path: Path):
    results = [
        TriggerResult(TriggerStatus.NO_ACTION, None, None),
        TriggerResult(TriggerStatus.BLOCKED, "c1", ConsumptionState.BLOCKED, failure_reason="governance blocked"),
    ]
    watcher, sleeper, events = SequenceWatcher(results), StopAfter(2), []
    result = _runtime(tmp_path, watcher, sleeper, events).run()
    assert result.status is WatchRuntimeStatus.STOPPED
    assert result.iterations == watcher.calls == 2
    assert sleeper.calls == [5.0, 5.0]
    assert [json.loads(item)["watch_iteration"]["trigger_status"] for item in events] == ["NO_ACTION", "BLOCKED"]


def test_minimum_interval_is_enforced(tmp_path: Path):
    with pytest.raises(ValueError, match="at least 5"):
        _runtime(tmp_path, SequenceWatcher([]), lambda _: None, interval=4.99)
    with pytest.raises(ValueError, match="at least 5"):
        _runtime(tmp_path, SequenceWatcher([]), lambda _: None, interval=float("nan"))


def test_second_runtime_lock_is_blocked_and_owner_can_release(tmp_path: Path):
    path = tmp_path / "watch.lock"
    owner = WatcherRuntimeLock(path)
    assert owner.acquire()
    watcher = SequenceWatcher([])
    result = _runtime(tmp_path, watcher, lambda _: None, lock=WatcherRuntimeLock(path)).run()
    assert result.status is WatchRuntimeStatus.BLOCKED
    assert watcher.calls == 0
    owner.release()
    assert not path.exists()


def test_lock_released_after_normal_ctrl_c_stop(tmp_path: Path):
    path = tmp_path / "watch.lock"
    runtime = _runtime(tmp_path, SequenceWatcher([TriggerResult(TriggerStatus.NO_ACTION, None, None)]), StopAfter(1), lock=WatcherRuntimeLock(path))
    assert runtime.run().status is WatchRuntimeStatus.STOPPED
    assert not path.exists()


def test_lock_released_when_keyboard_interrupts_run_once(tmp_path: Path):
    path = tmp_path / "watch.lock"
    runtime = _runtime(tmp_path, SequenceWatcher([KeyboardInterrupt()]), lambda _: None, lock=WatcherRuntimeLock(path))
    result = runtime.run()
    assert result.status is WatchRuntimeStatus.STOPPED and result.iterations == 0
    assert not path.exists()


def test_error_waits_before_retry_and_serializes_compactly(tmp_path: Path):
    watcher, sleeper, events = SequenceWatcher([RuntimeError("secret prompt text")]), StopAfter(1), []
    result = _runtime(tmp_path, watcher, sleeper, events).run()
    payload = json.loads(events[0])["watch_iteration"]
    assert result.status is WatchRuntimeStatus.STOPPED
    assert sleeper.calls == [5.0]
    assert payload["trigger_status"] == "ERROR"
    assert payload["failure_reason"] == "watch iteration failed: RuntimeError"
    assert "secret" not in events[0] and "prompt text" not in events[0]


def test_event_and_runtime_serialization_are_stable_without_authority():
    event = WatchIterationEvent(datetime(2026, 1, 1, tzinfo=timezone.utc), 1, TriggerStatus.NO_ACTION, None, None, None)
    encoded = serialize_watch_iteration_event(event)
    assert encoded == serialize_watch_iteration_event(event)
    assert "allowed_scope" not in encoded and "acceptance_criteria" not in encoded and "prompt" not in encoded.lower()
    assert "APPROVED" not in encoded and '"DONE"' not in encoded
    runtime = serialize_watch_runtime_result(WatchRuntimeResult(WatchRuntimeStatus.STOPPED, 1))
    assert json.loads(runtime)["watch_runtime_result"]["status"] == "STOPPED"


def test_real_no_action_watcher_does_not_mutate_ai(tmp_path: Path):
    (tmp_path / ".ai/tasks/ready").mkdir(parents=True)
    (tmp_path / ".ai/tasks/review").mkdir(parents=True)
    handoff = tmp_path / ".ai/handoff"
    handoff.mkdir(parents=True)
    (handoff / "TO-CODEX.md").write_text("Status: WAITING\nCurrent AIDP Task: NONE\n", encoding="utf-8")
    (handoff / "TO-ARCHITECT.md").write_text("Status: WAITING\nTask: NONE\n", encoding="utf-8")
    subprocess.run(("git", "init", "-q", "-b", "watch-test"), cwd=tmp_path, check=True)
    subprocess.run(("git", "config", "user.name", "Test"), cwd=tmp_path, check=True)
    subprocess.run(("git", "config", "user.email", "test@localhost"), cwd=tmp_path, check=True)
    subprocess.run(("git", "add", "--", ".ai"), cwd=tmp_path, check=True)
    subprocess.run(("git", "commit", "-q", "-m", "fixture"), cwd=tmp_path, check=True)
    before = {path: path.read_bytes() for path in (tmp_path / ".ai").rglob("*") if path.is_file()}
    repository = AIDPRepository(tmp_path)
    events = []
    result = AIDPLocalWatcherRuntime(repository, watcher=AIDPWatchOnce(repository), interval_seconds=5,
                                     sleeper=StopAfter(1), event_sink=events.append).run()
    after = {path: path.read_bytes() for path in (tmp_path / ".ai").rglob("*") if path.is_file()}
    assert result.status is WatchRuntimeStatus.STOPPED
    assert before == after
    assert json.loads(events[0])["watch_iteration"]["trigger_status"] == "NO_ACTION"
