"""Isolated Trigger-to-Git-remote end-to-end acceptance harness."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, Protocol

from .acceptance import AcceptanceHarness
from .contracts import (
    AcceptanceStatus, ArchitectTaskContract, CleanupStatus, ContractInboxItem,
    TriggerPublisherAcceptanceResult, TriggerResult, TriggerStatus, utc_now,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import AIDPWatchOnce


TRIGGER_E2E_TASK_ID = "TASK-E2E-TRIGGER-0001"
TRIGGER_E2E_BRANCH = "aidp-trigger-publisher-e2e"
TRIGGER_E2E_PROBE_PATH = "tests/orchestration/trigger_e2e_probe.txt"
TRIGGER_E2E_PROBE_CONTENT = "AIDP_TRIGGER_PUBLISHER_E2E_OK\n"


class WatcherBoundary(Protocol):
    def run_once(self) -> TriggerResult: ...


WatcherFactory = Callable[[AIDPRepository, Path, float], WatcherBoundary]


class TriggerPublisherAcceptanceHarness:
    def __init__(self, source_root: Path, *, timeout_seconds: float = 900.0,
                 preserve_on_failure: bool = True, watcher_factory: WatcherFactory | None = None):
        self.source_root = source_root.resolve()
        self.timeout_seconds = timeout_seconds
        self.preserve_on_failure = preserve_on_failure
        self.watcher_factory = watcher_factory

    def run(self) -> TriggerPublisherAcceptanceResult:
        fixture_parent = Path(tempfile.mkdtemp(prefix="aidp-acceptance-e2e-trigger-publisher-"))
        repository_root, remote_root = fixture_parent / "repository", fixture_parent / "origin.git"
        before = self._source_snapshot()
        first = second = None
        execution_commit = envelope_commit = envelope_path = remote_head = None
        envelope_verified = probe_verified = idempotency = False
        failure_reason = None
        try:
            self.build_fixture(repository_root, remote_root)
            self._verify_remote_guard(repository_root, remote_root)
            repository = AIDPRepository(repository_root)
            runtime_root = LocalRuntimeStore.for_repository(repository_root).root
            self.write_contract(runtime_root, self.build_contract(repository))
            watcher = self._watcher(repository, runtime_root)
            first = watcher.run_once()
            publish = first.publish_result
            if first.status is not TriggerStatus.PUBLISHED or publish is None:
                raise RuntimeError("first watcher run did not publish")
            execution_commit = publish.execution_commit
            envelope_commit = publish.review_envelope_commit
            envelope_path = publish.review_envelope_path
            if not execution_commit or not envelope_commit or not envelope_path:
                raise RuntimeError("publish result is incomplete")
            remote_head, envelope_verified, probe_verified = self.verify_remote(
                remote_root, execution_commit, envelope_commit, envelope_path,
                first.contract_id or "", publish.branch,
            )
            before_second_head = remote_head
            second = watcher.run_once()
            after_second_head = self._remote_head(remote_root, TRIGGER_E2E_BRANCH)
            idempotency = (
                second.status is TriggerStatus.BLOCKED
                and second.failure_reason is not None
                and "consum" in second.failure_reason.lower()
                and after_second_head == before_second_head
                and len(self._remote_envelopes(remote_root, after_second_head)) == 1
            )
            source_unchanged = self._source_snapshot() == before
            checks = (
                (envelope_verified, "remote review envelope verification failed"),
                (probe_verified, "remote probe verification failed"),
                (idempotency, "second watcher run was not idempotent"),
                (source_unchanged, "source AIDP or source remote changed"),
            )
            failure_reason = next((reason for passed, reason in checks if not passed), None)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            source_unchanged = self._source_snapshot() == before
            failure_reason = str(exc)

        passed = failure_reason is None
        cleanup = self._cleanup(fixture_parent, passed)
        if cleanup is CleanupStatus.FAILED:
            passed = False
            failure_reason = failure_reason or "temporary fixture cleanup failed"
        return TriggerPublisherAcceptanceResult(
            AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL, first, second,
            execution_commit, envelope_commit, envelope_path, TRIGGER_E2E_BRANCH,
            remote_head, envelope_verified, probe_verified, idempotency,
            source_unchanged, cleanup, str(repository_root), str(remote_root), failure_reason,
        )

    @staticmethod
    def build_fixture(repository_root: Path, remote_root: Path) -> None:
        repository_root.mkdir(parents=True)
        subprocess.run(("git", "init", "--bare", "-q", str(remote_root)), check=True)
        handoff = repository_root / ".ai/handoff"
        (repository_root / ".ai/tasks/ready").mkdir(parents=True)
        (repository_root / ".ai/tasks/review").mkdir(parents=True)
        handoff.mkdir(parents=True)
        (handoff / "TO-CODEX.md").write_text("Status: WAITING\nCurrent AIDP Task: NONE\nCurrent Phase: IDLE / WAITING\n", encoding="utf-8")
        (handoff / "TO-ARCHITECT.md").write_text("Status: WAITING\nTask: NONE\n", encoding="utf-8")
        probe = repository_root / TRIGGER_E2E_PROBE_PATH
        probe.parent.mkdir(parents=True)
        probe.write_text("PENDING\n", encoding="utf-8")
        _run_git(repository_root, "init", "-q", "-b", TRIGGER_E2E_BRANCH)
        _run_git(repository_root, "config", "user.name", "AIDP Trigger E2E Harness")
        _run_git(repository_root, "config", "user.email", "aidp-trigger-e2e@localhost")
        _run_git(repository_root, "add", "--", ".ai", TRIGGER_E2E_PROBE_PATH)
        _run_git(repository_root, "commit", "-q", "-m", "test: initialize Trigger Publisher E2E fixture")
        _run_git(repository_root, "remote", "add", "origin", str(remote_root.resolve()))
        _run_git(repository_root, "push", "-q", "-u", "origin", TRIGGER_E2E_BRANCH)

    @staticmethod
    def build_contract(repository: AIDPRepository) -> ArchitectTaskContract:
        return ArchitectTaskContract(
            TRIGGER_E2E_TASK_ID, "Trigger Publisher E2E Probe", "acceptance-e2e",
            repository.head, (TRIGGER_E2E_PROBE_PATH,),
            (".ai/**", "frontend/**", "core/**", "application/**"),
            ("git diff --check",),
            (f"Change only {TRIGGER_E2E_PROBE_PATH}", "Set its exact content to AIDP_TRIGGER_PUBLISHER_E2E_OK"),
            False, utc_now(),
        )

    @staticmethod
    def write_contract(runtime_root: Path, contract: ArchitectTaskContract) -> Path:
        item = ContractInboxItem("trigger-publisher-e2e-contract-0001", contract, utc_now())
        value = asdict(contract)
        path = runtime_root / "contract-inbox" / f"{item.contract_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"contract_inbox_item": {
            "contract_id": item.contract_id, "contract_type": "architect_task",
            "contract": value, "received_at": item.received_at,
        }}
        path.write_text(json.dumps(payload, default=_json_default, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def verify_remote(self, remote: Path, execution_commit: str, envelope_commit: str,
                      envelope_path: str, contract_id: str, branch: str) -> tuple[str, bool, bool]:
        if branch != TRIGGER_E2E_BRANCH or contract_id != "trigger-publisher-e2e-contract-0001":
            raise RuntimeError("published identity does not match fixture")
        remote_head = self._remote_head(remote, branch)
        if remote_head != envelope_commit:
            raise RuntimeError("remote HEAD does not match review envelope commit")
        ancestor = subprocess.run(("git", "--git-dir", str(remote), "merge-base", "--is-ancestor", execution_commit, remote_head))
        if ancestor.returncode != 0:
            raise RuntimeError("execution commit is not an ancestor of remote HEAD")
        envelope_raw = _bare_git(remote, "show", f"{remote_head}:{envelope_path}")
        envelope = json.loads(envelope_raw).get("architect_review_envelope")
        if not isinstance(envelope, dict):
            raise RuntimeError("remote review envelope is malformed")
        validations = envelope.get("validation_results")
        execution_paths = tuple(line for line in _bare_git(
            remote, "diff-tree", "--no-commit-id", "--name-only", "-r", execution_commit
        ).splitlines() if line)
        envelope_paths = tuple(line for line in _bare_git(
            remote, "diff-tree", "--no-commit-id", "--name-only", "-r", envelope_commit
        ).splitlines() if line)
        envelope_verified = (
            envelope.get("task_id") == TRIGGER_E2E_TASK_ID
            and isinstance(envelope.get("execution_id"), str) and bool(envelope["execution_id"])
            and envelope.get("changed_files") == [TRIGGER_E2E_PROBE_PATH]
            and envelope.get("execution_status") == "SUCCESS"
            and envelope.get("scope_compliance") == "COMPLIANT"
            and isinstance(validations, list) and bool(validations)
            and all(isinstance(v, dict) and v.get("passed") is True for v in validations)
            and envelope.get("intended_next_state") == "READY_FOR_ARCHITECT"
            and execution_paths == (TRIGGER_E2E_PROBE_PATH,)
            and envelope_paths == (envelope_path,)
            and "APPROVED" not in envelope_raw and '"DONE"' not in envelope_raw
        )
        probe_verified = _bare_git(remote, "show", f"{remote_head}:{TRIGGER_E2E_PROBE_PATH}") == TRIGGER_E2E_PROBE_CONTENT.rstrip("\n")
        return remote_head, envelope_verified, probe_verified

    @staticmethod
    def _verify_remote_guard(repository: Path, remote: Path) -> None:
        if _git(repository, "remote", "get-url", "origin") != str(remote.resolve()):
            raise RuntimeError("origin is not the isolated temporary bare repository")
        if _bare_git(remote, "rev-parse", "--is-bare-repository") != "true":
            raise RuntimeError("temporary origin is not bare")

    def _watcher(self, repository: AIDPRepository, runtime: Path) -> WatcherBoundary:
        if self.watcher_factory is not None:
            return self.watcher_factory(repository, runtime, self.timeout_seconds)
        return AIDPWatchOnce(repository, runtime_root=runtime, timeout_seconds=self.timeout_seconds)

    @staticmethod
    def _remote_head(remote: Path, branch: str) -> str:
        return _bare_git(remote, "rev-parse", f"refs/heads/{branch}")

    @staticmethod
    def _remote_envelopes(remote: Path, head: str) -> tuple[str, ...]:
        output = _bare_git(remote, "ls-tree", "-r", "--name-only", head, ".ai/orchestration/review-inbox")
        return tuple(line for line in output.splitlines() if line)

    def _source_snapshot(self) -> tuple[tuple[str, str], ...]:
        values: list[tuple[str, str]] = []
        for relative in (Path(".ai/tasks"), Path(".ai/handoff")):
            root = self.source_root / relative
            if root.exists():
                for path in sorted(item for item in root.rglob("*") if item.is_file()):
                    values.append((path.relative_to(self.source_root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
        try:
            origin = _git(self.source_root, "remote", "get-url", "origin")
        except subprocess.CalledProcessError:
            origin = ""
        values.append(("@origin", origin))
        return tuple(values)

    def _cleanup(self, root: Path, passed: bool) -> CleanupStatus:
        if not passed and self.preserve_on_failure:
            return CleanupStatus.PRESERVED
        try:
            AcceptanceHarness.remove_fixture(root)
        except (OSError, ValueError):
            return CleanupStatus.FAILED
        return CleanupStatus.CLEANED


def serialize_trigger_publisher_acceptance_result(result: TriggerPublisherAcceptanceResult) -> str:
    return json.dumps({"trigger_publisher_acceptance_result": asdict(result)}, default=_json_default, sort_keys=True)


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _bare_git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", "--git-dir", str(root), *args), text=True, stderr=subprocess.STDOUT).strip()


def _json_default(value: object) -> object:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    if isinstance(value, Path): return str(value)
    raise TypeError(type(value).__name__)
