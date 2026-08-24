from __future__ import annotations

import json
import subprocess
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from aidp_orchestration.architect_ingress import ArchitectGitIngress, PARSER_POLICY
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
    assert state.is_file()
    assert "secret" not in state.read_text(encoding="utf-8")


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


def test_malformed_historical_contract_is_rejected_once_and_valid_successor_proceeds(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    malformed_path = ".ai/orchestration/architect-contracts/architect-ingress-invalid.json"
    _commit_contract(architect, malformed_path, '{"contract_inbox_item":{"contract_id":"architect-ingress-invalid"}}', "invalid historical contract")
    successor = ContractInboxItem(
        "architect-ingress-successor",
        replace(contract, task_id="TASK-E2E-TRIGGER-0002"),
        datetime.now(timezone.utc),
    )
    _commit_contract(
        architect,
        ".ai/orchestration/architect-contracts/architect-ingress-successor.json",
        serialize_contract_inbox_item(successor),
        "valid successor contract",
    )
    result = ingress.run_once()
    assert result.status is IngressStatus.MATERIALIZED
    assert result.contract_id == "architect-ingress-successor"
    events_before = (runtime / "architect-ingress.jsonl").read_text(encoding="utf-8").splitlines()
    rejected = [
        json.loads(line)["architect_ingress_event"] for line in events_before
        if json.loads(line)["architect_ingress_event"].get("remote_path") == malformed_path
    ]
    assert len(rejected) == 1 and rejected[0]["status"] == "BLOCKED"
    assert rejected[0]["identity_kind"] == "rejection"
    assert rejected[0]["contract_id"].startswith("rejected-path-sha256:")
    assert len(LocalContractInbox(runtime).pending()) == 2
    assert ingress.run_once().status is IngressStatus.NO_ACTION
    assert (runtime / "architect-ingress.jsonl").read_text(encoding="utf-8").splitlines() == events_before


def test_bom_contract_is_reconsidered_once_after_parser_policy_upgrade(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    item = ContractInboxItem(
        "architect-task-0112-retry-8", replace(contract, task_id="TASK-E2E-TRIGGER-0002"),
        datetime.now(timezone.utc),
    )
    relative = ".ai/orchestration/architect-contracts/TASK-0112-retry-8.json"
    path = architect / relative
    path.write_bytes(b"\xef\xbb\xbf" + serialize_contract_inbox_item(item).encode("utf-8"))
    _git(architect, "add", "--", relative)
    _git(architect, "commit", "-m", "BOM contract")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)
    commit = _git(architect, "rev-parse", "HEAD")
    blob = _git(architect, "rev-parse", f"{commit}:{relative}")
    legacy = {"architect_ingress_event": {
        "contract_id": "rejected-path-sha256:legacy", "remote_commit": commit,
        "blob_id": blob, "status": "BLOCKED", "timestamp": "2026-01-01T00:00:00+00:00",
        "reason": "remote contract rejected: JSONDecodeError", "identity_kind": "rejection",
        "remote_path": relative,
    }}
    with (runtime / "architect-ingress.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(legacy) + "\n")
    result = ingress.run_once()
    assert result.status is IngressStatus.MATERIALIZED
    assert result.contract_id == "architect-task-0112-retry-8"
    assert ingress.run_once().status is IngressStatus.NO_ACTION


def test_still_invalid_legacy_rejection_is_versioned_then_suppressed(tmp_path: Path):
    repository, _remote, architect, runtime, _contract = _setup(tmp_path)
    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().status is IngressStatus.MATERIALIZED
    relative = ".ai/orchestration/architect-contracts/TASK-E2E-invalid-bom.json"
    path = architect / relative
    path.write_bytes(b"\xef\xbb\xbf{")
    _git(architect, "add", "--", relative)
    _git(architect, "commit", "-m", "invalid BOM contract")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)
    commit = _git(architect, "rev-parse", "HEAD")
    blob = _git(architect, "rev-parse", f"{commit}:{relative}")
    state = runtime / "architect-ingress.jsonl"
    legacy = {"architect_ingress_event": {
        "contract_id": "rejected-path-sha256:legacy-invalid", "remote_commit": commit,
        "blob_id": blob, "status": "BLOCKED", "timestamp": "2026-01-01T00:00:00+00:00",
        "reason": "old parser", "identity_kind": "rejection", "remote_path": relative,
    }}
    with state.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(legacy) + "\n")
    assert ingress.run_once().status is IngressStatus.BLOCKED
    events = [json.loads(line)["architect_ingress_event"] for line in state.read_text(encoding="utf-8").splitlines()]
    assert len([event for event in events if event.get("remote_path") == relative and event.get("parser_policy") == PARSER_POLICY]) == 1
    count = len(events)
    assert ingress.run_once().status is IngressStatus.NO_ACTION
    assert len(state.read_text(encoding="utf-8").splitlines()) == count


def test_real_filename_convention_tolerates_legacy_blocked_history(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    contract_root = ".ai/orchestration/architect-contracts"
    original_path = f"{contract_root}/{INGRESS_E2E_CONTRACT_ID}.json"
    _git(architect, "rm", "--", original_path)

    v1 = ContractInboxItem(
        "architect-task-0112-v1", contract, datetime.now(timezone.utc),
    )
    retry2 = ContractInboxItem(
        "architect-task-0112-retry-2",
        replace(contract, task_id="TASK-E2E-TRIGGER-0002"),
        datetime.now(timezone.utc),
    )
    paths = {
        "TASK-0112.json": serialize_contract_inbox_item(v1),
        "TASK-0112-retry-1.json": '{"contract_inbox_item":{"contract_id":"architect-task-0112-retry-1"}}',
        "TASK-0112-retry-2.json": serialize_contract_inbox_item(retry2),
    }
    for filename, content in paths.items():
        path = architect / contract_root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        _git(architect, "add", "--", path.relative_to(architect).as_posix())
    _git(architect, "commit", "-m", "real architect contract naming")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)

    commit = _git(architect, "rev-parse", "HEAD")
    blobs = {
        filename: _git(architect, "rev-parse", f"{commit}:{contract_root}/{filename}")
        for filename in paths
    }
    state = runtime / "architect-ingress.jsonl"
    state.parent.mkdir(parents=True, exist_ok=True)
    legacy_events = [
        {
            "contract_id": "architect-task-0112-v1",
            "blob_id": blobs["TASK-0112.json"],
            "status": "MATERIALIZED",
        },
        {
            "contract_id": "TASK-0112-retry-1",
            "blob_id": blobs["TASK-0112-retry-1.json"],
            "status": "BLOCKED",
        },
        {
            "contract_id": "TASK-0112-retry-2",
            "blob_id": blobs["TASK-0112-retry-2.json"],
            "status": "BLOCKED",
        },
        {
            "contract_id": "TASK-0112",
            "blob_id": blobs["TASK-0112.json"],
            "status": "BLOCKED",
        },
    ]
    state.write_text("".join(
        json.dumps({"architect_ingress_event": {
            **event, "remote_commit": commit, "timestamp": "2026-01-01T00:00:00+00:00",
            "reason": "legacy Rework #2 observation",
        }}, sort_keys=True) + "\n"
        for event in legacy_events
    ), encoding="utf-8")

    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    result = ingress.run_once()
    assert result.status is IngressStatus.MATERIALIZED
    assert result.contract_id == "architect-task-0112-retry-2"
    assert LocalContractInbox(runtime).pending()[0].contract_id == "architect-task-0112-retry-2"

    events = [json.loads(line)["architect_ingress_event"] for line in state.read_text(encoding="utf-8").splitlines()]
    rejected = [event for event in events if event.get("remote_path", "").endswith("TASK-0112-retry-1.json")]
    assert len(rejected) == 1
    assert rejected[0]["identity_kind"] == "rejection"
    assert rejected[0]["contract_id"].startswith("rejected-path-sha256:")
    event_count = len(events)
    assert ingress.run_once().status is IngressStatus.NO_ACTION
    assert len(state.read_text(encoding="utf-8").splitlines()) == event_count


def test_mutated_blob_uses_validated_embedded_identity_when_filename_differs(tmp_path: Path):
    repository, _remote, architect, runtime, contract = _setup(tmp_path)
    old_path = f".ai/orchestration/architect-contracts/{INGRESS_E2E_CONTRACT_ID}.json"
    new_path = ".ai/orchestration/architect-contracts/TASK-0112-retry-2.json"
    item = ContractInboxItem("architect-task-0112-retry-2", contract, datetime.now(timezone.utc))
    _git(architect, "rm", "--", old_path)
    target = architect / new_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(serialize_contract_inbox_item(item), encoding="utf-8")
    _git(architect, "add", "--", new_path)
    _git(architect, "commit", "-m", "publish differently named contract")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)

    ingress = ArchitectGitIngress(AIDPRepository(repository), branch=INGRESS_E2E_BRANCH, runtime_root=runtime)
    assert ingress.run_once().contract_id == "architect-task-0112-retry-2"
    target.write_text(serialize_contract_inbox_item(replace(item, contract=replace(contract, title="Changed"))), encoding="utf-8")
    _git(architect, "add", "--", new_path)
    _git(architect, "commit", "-m", "mutate differently named contract")
    _git(architect, "push", "origin", INGRESS_E2E_BRANCH)
    result = ingress.run_once()
    assert result.status is IngressStatus.BLOCKED
    assert result.contract_id == "architect-task-0112-retry-2"
    assert result.failure_reason == "contract_id content mutated"


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
