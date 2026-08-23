from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    AIDPState, AcceptanceStatus, CleanupStatus, ConsumptionState, PublishResult,
    TriggerResult, TriggerStatus,
)
from aidp_orchestration.trigger_publisher import LocalContractInbox
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.trigger_publisher_acceptance import (
    TRIGGER_E2E_BRANCH, TRIGGER_E2E_PROBE_CONTENT, TRIGGER_E2E_PROBE_PATH,
    TRIGGER_E2E_TASK_ID, TriggerPublisherAcceptanceHarness,
    serialize_trigger_publisher_acceptance_result,
)


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


class PublishingWatcher:
    def __init__(self, root: Path):
        self.root = root
        self.calls = 0
        self.executions = 0
        self.pushes = 0

    def run_once(self) -> TriggerResult:
        self.calls += 1
        if self.calls > 1:
            return TriggerResult(TriggerStatus.BLOCKED, "trigger-publisher-e2e-contract-0001", ConsumptionState.REVIEW_PUBLISHED, failure_reason="contract_id was already consumed")
        self.executions += 1
        probe = self.root / TRIGGER_E2E_PROBE_PATH
        probe.write_text(TRIGGER_E2E_PROBE_CONTENT, encoding="utf-8")
        _git(self.root, "add", "--", TRIGGER_E2E_PROBE_PATH)
        _git(self.root, "commit", "-m", "fixture execution")
        execution_commit = _git(self.root, "rev-parse", "HEAD")
        execution_id = "trigger-e2e-execution"
        relative = f".ai/orchestration/review-inbox/{TRIGGER_E2E_TASK_ID}-{execution_id}.json"
        path = self.root / relative
        path.parent.mkdir(parents=True)
        envelope = {"architect_review_envelope": {
            "task_id": TRIGGER_E2E_TASK_ID, "execution_id": execution_id,
            "branch": TRIGGER_E2E_BRANCH, "start_commit": execution_commit,
            "resulting_commit": execution_commit, "execution_status": "SUCCESS",
            "changed_files": [TRIGGER_E2E_PROBE_PATH], "scope_compliance": "COMPLIANT",
            "validation_results": [{"name": "git diff --check", "passed": True, "detail": "passed"}],
            "failure_reason": None, "intended_next_state": "READY_FOR_ARCHITECT",
            "published_at": "2026-01-01T00:00:00+00:00",
        }}
        path.write_text(json.dumps(envelope, sort_keys=True) + "\n", encoding="utf-8")
        _git(self.root, "add", "--", relative)
        _git(self.root, "commit", "-m", "fixture review envelope")
        review_commit = _git(self.root, "rev-parse", "HEAD")
        _git(self.root, "push", "origin", TRIGGER_E2E_BRANCH)
        self.pushes += 1
        publish = PublishResult(TRIGGER_E2E_BRANCH, execution_commit, relative, review_commit, "PUSHED", AIDPState.READY_FOR_ARCHITECT)
        return TriggerResult(TriggerStatus.PUBLISHED, "trigger-publisher-e2e-contract-0001", ConsumptionState.REVIEW_PUBLISHED, publish_result=publish)


class BlockingWatcher:
    def run_once(self) -> TriggerResult:
        return TriggerResult(TriggerStatus.BLOCKED, None, None, failure_reason="blocked fixture")


def _source(root: Path) -> None:
    path = root / ".ai/handoff/TO-CODEX.md"
    path.parent.mkdir(parents=True)
    path.write_text("Status: WAITING\n", encoding="utf-8")


def test_fixture_uses_temporary_bare_origin_and_waiting_contract_inbox(tmp_path: Path):
    repository, remote = tmp_path / "repository", tmp_path / "origin.git"
    TriggerPublisherAcceptanceHarness.build_fixture(repository, remote)
    TriggerPublisherAcceptanceHarness._verify_remote_guard(repository, remote)
    assert _git(repository, "branch", "--show-current") == TRIGGER_E2E_BRANCH
    assert AIDPRepository(repository).inspect().state is AIDPState.WAITING
    assert _git(repository, "status", "--porcelain=v1") == ""
    assert subprocess.check_output(("git", "--git-dir", str(remote), "rev-parse", "--is-bare-repository"), text=True).strip() == "true"
    harness = TriggerPublisherAcceptanceHarness(tmp_path)
    contract = harness.build_contract(AIDPRepository(repository))
    runtime = repository / ".git/aidp-orchestration/runtime"
    harness.write_contract(runtime, contract)
    assert LocalContractInbox(runtime).pending()[0].contract.task_id == TRIGGER_E2E_TASK_ID


def test_remote_guard_rejects_non_fixture_origin(tmp_path: Path):
    repository, remote, other = tmp_path / "repository", tmp_path / "origin.git", tmp_path / "other.git"
    TriggerPublisherAcceptanceHarness.build_fixture(repository, remote)
    subprocess.run(("git", "init", "--bare", "-q", str(other)), check=True)
    _git(repository, "remote", "set-url", "origin", str(other))
    with pytest.raises(RuntimeError, match="isolated"):
        TriggerPublisherAcceptanceHarness._verify_remote_guard(repository, remote)


def test_harness_verifies_remote_and_second_run_is_idempotent(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    _source(source)
    holder = {}
    def factory(repository, _runtime, _timeout):
        watcher = PublishingWatcher(repository.root)
        holder["watcher"] = watcher
        return watcher
    result = TriggerPublisherAcceptanceHarness(source, watcher_factory=factory).run()
    assert result.status is AcceptanceStatus.PASS
    assert result.remote_head == result.review_envelope_commit
    assert result.remote_envelope_verified and result.remote_probe_verified
    assert result.idempotency_verified and result.source_aidp_unchanged
    assert holder["watcher"].calls == 2
    assert holder["watcher"].executions == holder["watcher"].pushes == 1
    assert result.cleanup_status is CleanupStatus.CLEANED
    assert not Path(result.temporary_repository).exists()
    assert not Path(result.temporary_remote).exists()


def test_failure_preserves_both_repositories(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    _source(source)
    result = TriggerPublisherAcceptanceHarness(source, watcher_factory=lambda *_: BlockingWatcher()).run()
    try:
        assert result.status is AcceptanceStatus.FAIL
        assert result.cleanup_status is CleanupStatus.PRESERVED
        assert Path(result.temporary_repository).is_dir()
        assert Path(result.temporary_remote).is_dir()
    finally:
        from aidp_orchestration.acceptance import AcceptanceHarness
        AcceptanceHarness.remove_fixture(Path(result.temporary_repository).parent)


def test_acceptance_serialization_is_stable_and_has_no_approval(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    _source(source)
    result = TriggerPublisherAcceptanceHarness(source, watcher_factory=lambda repository, *_: PublishingWatcher(repository.root)).run()
    encoded = serialize_trigger_publisher_acceptance_result(result)
    payload = json.loads(encoded)["trigger_publisher_acceptance_result"]
    assert encoded == serialize_trigger_publisher_acceptance_result(result)
    assert payload["status"] == "PASS"
    assert payload["remote_envelope_verified"] is True
    assert "prompt" not in encoded.lower() and "APPROVED" not in encoded
