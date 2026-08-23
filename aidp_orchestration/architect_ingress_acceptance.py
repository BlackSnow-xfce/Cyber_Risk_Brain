"""Isolated Architect Git ingress acceptance harness (no Codex execution)."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from dataclasses import asdict, replace
from datetime import datetime
from enum import Enum
from pathlib import Path

from .acceptance import AcceptanceHarness
from .architect_ingress import ArchitectGitIngress
from .contracts import (
    AcceptanceStatus, ArchitectIngressAcceptanceResult, ArchitectTaskContract,
    CleanupStatus, ContractInboxItem, IngressStatus, WriterAction, WriterDecision,
    WriterResult, utc_now,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .trigger_publisher import AIDPWatchOnce, LocalContractInbox, serialize_contract_inbox_item


INGRESS_E2E_BRANCH = "aidp/architect-contracts"
INGRESS_E2E_CONTRACT_ID = "architect-ingress-e2e-contract-0001"
INGRESS_E2E_TASK_ID = "TASK-E2E-TRIGGER-0001"


class _ObservingBlockedWriter:
    def __init__(self):
        self.task_id: str | None = None

    def materialize_task(self, contract: ArchitectTaskContract) -> WriterResult:
        self.task_id = contract.task_id
        reason = "acceptance observation stops before Writer materialization"
        return WriterResult(WriterDecision(WriterAction.BLOCKED, contract.task_id, "fixture", contract.expected_head, reason), failure_reason=reason)

    def materialize_rework(self, contract):
        raise RuntimeError("unexpected rework contract")


class ArchitectIngressAcceptanceHarness:
    def __init__(self, source_root: Path, *, preserve_on_failure: bool = True):
        self.source_root = source_root.resolve()
        self.preserve_on_failure = preserve_on_failure

    def run(self) -> ArchitectIngressAcceptanceResult:
        parent = Path(tempfile.mkdtemp(prefix="aidp-acceptance-e2e-architect-ingress-"))
        repository_root, remote_root, architect_root = parent / "repository", parent / "origin.git", parent / "architect"
        before = self._source_snapshot()
        remote_commit = None
        ingress_status = IngressStatus.ERROR
        second_status = None
        materialized = verified = mutation_guard = False
        failure_reason = None
        try:
            self.build_fixture(repository_root, remote_root)
            contract = self.build_contract(AIDPRepository(repository_root))
            remote_commit = self.publish_remote_contract(remote_root, architect_root, contract)
            runtime = LocalRuntimeStore.for_repository(repository_root).root
            ingress = ArchitectGitIngress(AIDPRepository(repository_root), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
            first = ingress.run_once()
            ingress_status = first.status
            materialized = bool(first.local_inbox_path and Path(first.local_inbox_path).is_file())
            pending = LocalContractInbox(runtime).pending()
            observer = _ObservingBlockedWriter()
            watch_result = AIDPWatchOnce(AIDPRepository(repository_root), writer=observer, runtime_root=runtime).run_once()
            verified = (
                len(pending) == 1 and pending[0].contract_id == INGRESS_E2E_CONTRACT_ID
                and pending[0].contract == contract and observer.task_id == contract.task_id
                and watch_result.contract_id == INGRESS_E2E_CONTRACT_ID
            )
            second = ingress.run_once()
            second_status = second.status
            mutated = replace(contract, title="Mutated Ingress Contract")
            self.update_remote_contract(architect_root, mutated)
            mutation = ingress.run_once()
            mutation_guard = mutation.status is IngressStatus.BLOCKED and mutation.contract_id == INGRESS_E2E_CONTRACT_ID
            source_unchanged = self._source_snapshot() == before
            checks = (
                (first.status is IngressStatus.MATERIALIZED, "first ingress did not materialize"),
                (materialized, "local inbox file is missing"),
                (verified, "AIDPWatchOnce did not observe the same contract"),
                (second.status is IngressStatus.NO_ACTION, "duplicate ingress was not idempotent"),
                (mutation_guard, "mutated contract_id was not blocked"),
                (source_unchanged, "source AIDP changed"),
            )
            failure_reason = next((reason for passed, reason in checks if not passed), None)
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
            source_unchanged = self._source_snapshot() == before
            failure_reason = str(exc)
        passed = failure_reason is None
        cleanup = self._cleanup(parent, passed)
        if cleanup is CleanupStatus.FAILED:
            passed = False
            failure_reason = failure_reason or "temporary fixture cleanup failed"
        return ArchitectIngressAcceptanceResult(
            AcceptanceStatus.PASS if passed else AcceptanceStatus.FAIL,
            INGRESS_E2E_BRANCH, remote_commit, INGRESS_E2E_CONTRACT_ID, ingress_status,
            materialized, verified, second_status, mutation_guard, source_unchanged,
            cleanup, str(repository_root), str(remote_root), failure_reason,
        )

    @staticmethod
    def build_fixture(repository: Path, remote: Path) -> None:
        repository.mkdir(parents=True)
        subprocess.run(("git", "init", "--bare", "-q", str(remote)), check=True)
        handoff = repository / ".ai/handoff"
        (repository / ".ai/tasks/ready").mkdir(parents=True)
        (repository / ".ai/tasks/review").mkdir(parents=True)
        handoff.mkdir(parents=True)
        (handoff / "TO-CODEX.md").write_text("Status: WAITING\nCurrent AIDP Task: NONE\n", encoding="utf-8")
        (handoff / "TO-ARCHITECT.md").write_text("Status: WAITING\nTask: NONE\n", encoding="utf-8")
        _run_git(repository, "init", "-q", "-b", "ingress-fixture")
        _run_git(repository, "config", "user.name", "AIDP Ingress E2E")
        _run_git(repository, "config", "user.email", "aidp-ingress@localhost")
        _run_git(repository, "add", "--", ".ai")
        _run_git(repository, "commit", "-q", "-m", "test: initialize ingress fixture")
        _run_git(repository, "remote", "add", "origin", str(remote.resolve()))
        _run_git(repository, "push", "-q", "-u", "origin", "ingress-fixture")

    @staticmethod
    def build_contract(repository: AIDPRepository) -> ArchitectTaskContract:
        return ArchitectTaskContract(
            INGRESS_E2E_TASK_ID, "Architect Ingress E2E", "acceptance-e2e", repository.head,
            ("tests/orchestration/ingress_probe.txt",), ("no product files",),
            ("git diff --check",), ("Verify ingress transport",), False, utc_now(),
        )

    @staticmethod
    def publish_remote_contract(remote: Path, architect: Path, contract: ArchitectTaskContract) -> str:
        subprocess.run(("git", "clone", "-q", str(remote), str(architect)), check=True)
        _run_git(architect, "config", "user.name", "Architect Fixture")
        _run_git(architect, "config", "user.email", "architect@localhost")
        _run_git(architect, "switch", "-q", "-c", INGRESS_E2E_BRANCH, "origin/ingress-fixture")
        ArchitectIngressAcceptanceHarness._write_remote_contract(architect, contract)
        _run_git(architect, "add", "--", f".ai/orchestration/architect-contracts/{INGRESS_E2E_CONTRACT_ID}.json")
        _run_git(architect, "commit", "-q", "-m", "architect: publish E2E contract")
        _run_git(architect, "push", "-q", "origin", INGRESS_E2E_BRANCH)
        return _git(architect, "rev-parse", "HEAD")

    @staticmethod
    def update_remote_contract(architect: Path, contract: ArchitectTaskContract) -> None:
        ArchitectIngressAcceptanceHarness._write_remote_contract(architect, contract)
        _run_git(architect, "add", "--", f".ai/orchestration/architect-contracts/{INGRESS_E2E_CONTRACT_ID}.json")
        _run_git(architect, "commit", "-q", "-m", "architect: mutate E2E contract")
        _run_git(architect, "push", "-q", "origin", INGRESS_E2E_BRANCH)

    @staticmethod
    def _write_remote_contract(root: Path, contract: ArchitectTaskContract) -> None:
        path = root / ".ai/orchestration/architect-contracts" / f"{INGRESS_E2E_CONTRACT_ID}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(serialize_contract_inbox_item(ContractInboxItem(INGRESS_E2E_CONTRACT_ID, contract, utc_now())) + "\n", encoding="utf-8")

    def _source_snapshot(self) -> tuple[tuple[str, str], ...]:
        values = []
        for relative in (Path(".ai/tasks"), Path(".ai/handoff")):
            root = self.source_root / relative
            if root.exists():
                for path in sorted(item for item in root.rglob("*") if item.is_file()):
                    values.append((path.relative_to(self.source_root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
        return tuple(values)

    def _cleanup(self, root: Path, passed: bool) -> CleanupStatus:
        if not passed and self.preserve_on_failure: return CleanupStatus.PRESERVED
        try: AcceptanceHarness.remove_fixture(root)
        except (OSError, ValueError): return CleanupStatus.FAILED
        return CleanupStatus.CLEANED


def serialize_architect_ingress_acceptance_result(result: ArchitectIngressAcceptanceResult) -> str:
    return json.dumps({"architect_ingress_acceptance_result": asdict(result)}, default=_json_default, sort_keys=True)


def _run_git(root: Path, *args: str) -> None:
    subprocess.run(("git", *args), cwd=root, check=True, capture_output=True)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _json_default(value: object) -> object:
    if isinstance(value, datetime): return value.isoformat()
    if isinstance(value, Enum): return value.value
    raise TypeError(type(value).__name__)
