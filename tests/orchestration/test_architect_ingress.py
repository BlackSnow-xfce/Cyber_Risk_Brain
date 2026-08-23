from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from aidp_orchestration.architect_ingress import ArchitectGitIngress
from aidp_orchestration.architect_ingress_acceptance import (
    INGRESS_E2E_BRANCH, INGRESS_E2E_CONTRACT_ID, ArchitectIngressAcceptanceHarness,
    serialize_architect_ingress_acceptance_result,
)
from aidp_orchestration.contracts import (
    AcceptanceStatus, ArchitectIngressResult, ArchitectTaskContract, CleanupStatus,
    ContractInboxItem, IngressStatus, TriggerResult, TriggerStatus,
)
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.trigger_publisher import LocalContractInbox, serialize_contract_inbox_item
from aidp_orchestration.watcher_runtime import AIDPLocalWatcherRuntime, WatcherRuntimeLock


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _setup(tmp_path: Path):
    repository, remote, architect = tmp_path / "repository", tmp_path / "origin.git", tmp_path / "architect"
    ArchitectIngressAcceptanceHarness.build_fixture(repository, remote)
    contract = ArchitectIngressAcceptanceHarness.build_contract(AIDPRepository(repository))
    ArchitectIngressAcceptanceHarness.publish_remote_contract(remote, architect, contract)
    runtime = LocalRuntimeStore.for_repository(repository).root
    return repository, remote, architect, runtime, contract


def test_fetch_is_read_only_and_valid_contract_enters_local_inbox(tmp_path: Path):
    repository, _remote, _architect, runtime, contract = _setup(tmp_path)
    head, branch = _git(repository, "rev-parse", "HEAD"), _git(repository, "branch", "--show-current")
    result = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime).run_once()
    assert result.status is IngressStatus.MATERIALIZED
    assert _git(repository, "rev-parse", "HEAD") == head
    assert _git(repository, "branch", "--show-current") == branch
    assert _git(repository, "status", "--porcelain=v1") == ""
    assert LocalContractInbox(runtime).pending()[0].contract == contract


def test_duplicate_is_no_action_and_mutated_blob_is_blocked(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    assert ingress.run_once().status is IngressStatus.NO_ACTION
    ArchitectIngressAcceptanceHarness.update_remote_contract(architect, replace(contract, title="Changed"))
    mutation = ingress.run_once()
    assert mutation.status is IngressStatus.BLOCKED
    assert mutation.contract_id == INGRESS_E2E_CONTRACT_ID
    assert len(LocalContractInbox(runtime).pending()) == 1


def _commit_contract(architect: Path, relative: str, content: str, message: str) -> None:
    path = architect / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(architect, "add", "--", relative)
    _git(architect, "commit", "-m", message)
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)


def test_malformed_or_nested_contract_is_blocked(tmp_path: Path):
    repository, _remote, architect, runtime, _contract = _setup(tmp_path)
    _commit_contract(architect, ".ai/orchestration/architect-contracts/nested/bad.json", "{}", "bad nested contract")
    result = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime).run_once()
    assert result.status is IngressStatus.BLOCKED
    assert not (runtime / "contract-inbox").exists()


def test_unknown_validator_and_extra_prompt_field_are_blocked(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    path = architect / f".ai/orchestration/architect-contracts/{INGRESS_E2E_CONTRACT_ID}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["contract_inbox_item"]["contract"]["validation_requirements"] = ["unknown"]
    payload["contract_inbox_item"]["contract"]["prompt"] = "secret"
    path.write_text(json.dumps(payload), encoding="utf-8")
    _git(architect, "add", "--", path.relative_to(architect).as_posix())
    _git(architect, "commit", "-m", "invalid schema")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)
    result = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime).run_once()
    assert result.status is IngressStatus.BLOCKED
    assert not (runtime / "contract-inbox").exists()
    state = (runtime / "architect-ingress.jsonl")
    assert not state.exists() or "secret" not in state.read_text(encoding="utf-8")


def test_explicit_valid_branch_and_origin_are_required(tmp_path: Path):
    repository, _remote, _architect, runtime, _contract = _setup(tmp_path)
    try:
        ArchitectGitIngress(AIDPRepository(repository), branch="")
    except ValueError:
        pass
    else:
        raise AssertionError("empty branch accepted")
    _git(repository, "remote", "remove", "origin")
    result = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime).run_once()
    assert result.status is IngressStatus.BLOCKED


def test_at_most_one_new_contract_is_materialized(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    second = ContractInboxItem("architect-ingress-e2e-contract-0002", replace(contract, task_id="TASK-E2E-TRIGGER-0002"), datetime.now(timezone.utc))
    _commit_contract(architect, ".ai/orchestration/architect-contracts/architect-ingress-e2e-contract-0002.json", serialize_contract_inbox_item(second), "second contract")
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    assert len(LocalContractInbox(runtime).pending()) == 1


def test_watcher_composes_ingress_before_watch_once_and_no_action_remains_normal(tmp_path: Path):
    order, events = [], []
    class Ingress:
        def run_once(self):
            order.append("ingress")
            return ArchitectIngressResult(IngressStatus.NO_ACTION, None, "commit", None)
    class Watcher:
        def run_once(self):
            order.append("watcher")
            return TriggerResult(TriggerStatus.NO_ACTION, None, None)
    def stop(_seconds): raise KeyboardInterrupt
    result = AIDPLocalWatcherRuntime(AIDPRepository(tmp_path), ingress=Ingress(), watcher=Watcher(),
        interval_seconds=5, sleeper=stop, event_sink=events.append, lock=WatcherRuntimeLock(tmp_path / "lock")).run()
    assert order == ["ingress", "watcher"]
    payload = json.loads(events[0])["watch_iteration"]
    assert payload["trigger_status"] == "NO_ACTION" and payload["ingress_status"] == "NO_ACTION"
    assert "prompt" not in events[0].lower()


def test_acceptance_cleanup_source_integrity_and_serialization(tmp_path: Path):
    source = tmp_path / "source"
    handoff = source / ".ai/handoff/TO-CODEX.md"
    handoff.parent.mkdir(parents=True)
    handoff.write_text("Status: WAITING\n", encoding="utf-8")
    before = handoff.read_bytes()
    result = ArchitectIngressAcceptanceHarness(source).run()
    assert result.status is AcceptanceStatus.PASS
    assert result.source_aidp_unchanged and handoff.read_bytes() == before
    assert result.cleanup_status is CleanupStatus.CLEANED
    encoded = serialize_architect_ingress_acceptance_result(result)
    assert encoded == serialize_architect_ingress_acceptance_result(result)
    assert "prompt" not in encoded.lower() and "APPROVED" not in encoded and '"DONE"' not in encoded
    assert not Path(result.temporary_repository).exists() and not Path(result.temporary_remote).exists()


def test_acceptance_preserves_fixture_on_failure(tmp_path: Path):
    class FailingHarness(ArchitectIngressAcceptanceHarness):
        @staticmethod
        def publish_remote_contract(remote, architect, contract):
            raise RuntimeError("fixture failure")

    source = tmp_path / "source"
    source.mkdir()
    result = FailingHarness(source).run()
    try:
        assert result.status is AcceptanceStatus.FAIL
        assert result.cleanup_status is CleanupStatus.PRESERVED
        assert Path(result.temporary_repository).is_dir()
        assert Path(result.temporary_remote).is_dir()
    finally:
        from aidp_orchestration.acceptance import AcceptanceHarness
        AcceptanceHarness.remove_fixture(Path(result.temporary_repository).parent)
