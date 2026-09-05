from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    AIDPState, ArchitectFinding, ArchitectReviewDisposition, ArchitectReviewProvenance,
    ArchitectTaskContract, CodexExecutionResult, ConsumptionState, ControlPlaneAction,
    ControlPlaneDecision, ControlPlaneResult, TriggerStatus, WriterAction,
    WriterDecision, WriterResult, ExecutionStatus, ScopeCompliance, RunnerResult, RunnerStatus, ValidationResult,
    ExecutionAttemptV1, ExecutionHeartbeatV1, ExecutionSupervisionFailureV1,
    LegacyRecoveryAuthorizationV1, RecoveryAuthorizationV1,
    OrchestrationDecision, ReworkContract, canonical_digest,
)
from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.executor import GitInspector
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.trigger_publisher import (
    AIDPWatchOnce, ConsumptionStore, LocalContractInbox, serialize_trigger_result,
    GitReviewPublisher,
)


def _contract(task_id: str = "TASK-E2E-WRITER-0001") -> ArchitectTaskContract:
    return ArchitectTaskContract(
        task_id, "Probe", "IMPLEMENTATION", "a" * 40,
        ("tests/orchestration/probe.txt",), ("no product files",),
        ("git diff --check",), ("probe exists",), False,
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _write_inbox(root: Path, contract_id: str = "contract-1", task_id: str = "TASK-E2E-WRITER-0001") -> None:
    contract = _contract(task_id)
    value = {
        "contract_inbox_item": {
            "contract_id": contract_id, "contract_type": "architect_task",
            "received_at": "2026-01-01T00:00:00+00:00",
            "contract": {
                "task_id": contract.task_id, "title": contract.title, "phase": contract.phase,
                "expected_head": contract.expected_head, "allowed_scope": list(contract.allowed_scope),
                "prohibited_actions": list(contract.prohibited_actions),
                "validation_requirements": list(contract.validation_requirements),
                "acceptance_criteria": list(contract.acceptance_criteria),
                "product_owner_gate": contract.product_owner_gate, "created_at": contract.created_at.isoformat(),
            },
        }
    }
    path = root / "contract-inbox" / "one.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


class FakeWriter:
    calls = 0

    def materialize_task(self, contract):
        self.calls += 1
        return WriterResult(WriterDecision(WriterAction.MATERIALIZE_READY, contract.task_id, "topic", "head", "ok"))

    def materialize_rework(self, contract):
        raise AssertionError("wrong writer path")


class FakeControlPlane:
    calls = 0

    def decide(self):
        return ControlPlaneDecision(ControlPlaneAction.EXECUTE, "TASK-E2E-WRITER-0001", AIDPState.READY_FOR_CODEX, "topic", "head", "ok")

    def run_once(self):
        self.calls += 1
        return ControlPlaneResult(self.decide(), ControlPlaneAction.READY_FOR_ARCHITECT)


class FakePublisher:
    calls = 0

    def commit_materialization(self, result):
        raise AssertionError("no materialized paths in fixture")

    def publish(self, result, expected_branch):
        from aidp_orchestration.contracts import PublishResult
        self.calls += 1
        return PublishResult(expected_branch, "exec", ".ai/orchestration/review-inbox/x.json", "review", "PUSHED", AIDPState.READY_FOR_ARCHITECT)


def test_empty_inbox_is_no_action(tmp_path: Path):
    watcher = AIDPWatchOnce(AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=FakeControlPlane(), publisher=FakePublisher(), runtime_root=tmp_path / "runtime", execution_lock_active=lambda: False)
    assert watcher.run_once().status is TriggerStatus.NO_ACTION


def test_contract_namespace_routes_to_only_the_matching_repository(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime, "infra-contract", "AIDP-INFRA-0002")
    product = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=FakeControlPlane(),
        publisher=FakePublisher(), runtime_root=runtime, execution_lock_active=lambda: False,
    )
    infrastructure = AIDPWatchOnce(
        AIDPRepository(tmp_path, task_namespace="infrastructure"), writer=FakeWriter(),
        control_plane=FakeControlPlane(), publisher=FakePublisher(), runtime_root=runtime,
        execution_lock_active=lambda: False,
    )
    assert product.run_once().status is TriggerStatus.NO_ACTION
    assert infrastructure.run_once().status is TriggerStatus.PUBLISHED
    assert ConsumptionStore(runtime).current("infra-contract") is ConsumptionState.REVIEW_PUBLISHED


def test_contract_is_consumed_exactly_once_across_restart(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    writer, control, publisher = FakeWriter(), FakeControlPlane(), FakePublisher()
    first = AIDPWatchOnce(AIDPRepository(tmp_path), writer=writer, control_plane=control, publisher=publisher, runtime_root=runtime, execution_lock_active=lambda: False).run_once()
    second = AIDPWatchOnce(AIDPRepository(tmp_path), writer=writer, control_plane=control, publisher=publisher, runtime_root=runtime, execution_lock_active=lambda: False).run_once()
    assert first.status is TriggerStatus.PUBLISHED
    assert second.status is TriggerStatus.NO_ACTION
    assert writer.calls == control.calls == publisher.calls == 1
    assert ConsumptionStore(runtime).current("contract-1") is ConsumptionState.REVIEW_PUBLISHED


def test_consumption_log_is_append_only_and_serialization_has_no_authority(tmp_path: Path):
    store = ConsumptionStore(tmp_path)
    store.append("c", ConsumptionState.RECEIVED, "received")
    store.append("c", ConsumptionState.BLOCKED, "blocked")
    assert len(store.path.read_text(encoding="utf-8").splitlines()) == 2
    result = AIDPWatchOnce(AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=FakeControlPlane(), publisher=FakePublisher(), runtime_root=tmp_path / "empty", execution_lock_active=lambda: False).run_once()
    encoded = serialize_trigger_result(result)
    assert encoded == serialize_trigger_result(result)
    assert "prompt" not in encoded.lower()
    assert "APPROVED" not in encoded and '"DONE"' not in encoded


def test_malformed_and_duplicate_contract_ids_fail_closed(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    original = runtime / "contract-inbox" / "one.json"
    (original.parent / "two.json").write_bytes(original.read_bytes())
    try:
        LocalContractInbox(runtime).pending()
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate contract_id accepted")


def test_contract_parser_accepts_one_utf8_bom_and_rejects_malformed_encoding(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    content = (runtime / "contract-inbox/one.json").read_bytes()
    assert LocalContractInbox.parse(b"\xef\xbb\xbf" + content).contract_id == "contract-1"
    with pytest.raises(UnicodeDecodeError):
        LocalContractInbox.parse(b"\x81" + content)


def test_product_owner_wait_never_publishes(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    control = FakeControlPlane()
    control.decide = lambda: ControlPlaneDecision(ControlPlaneAction.WAITING_FOR_PRODUCT_OWNER, "TASK-E2E-WRITER-0001", AIDPState.WAITING_FOR_PRODUCT_OWNER, "topic", "head", "gate")
    publisher = FakePublisher()
    result = AIDPWatchOnce(AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=control, publisher=publisher, runtime_root=runtime, execution_lock_active=lambda: False).run_once()
    assert result.status is TriggerStatus.BLOCKED
    assert publisher.calls == 0


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def test_success_commits_only_execution_and_envelope_then_pushes_origin(tmp_path: Path):
    repository_root, remote = tmp_path / "repo", tmp_path / "origin.git"
    repository_root.mkdir()
    _git(repository_root, "init", "-b", "topic")
    _git(repository_root, "config", "user.name", "AIDP Test")
    _git(repository_root, "config", "user.email", "aidp@example.invalid")
    probe = repository_root / "tests/orchestration/probe.txt"
    probe.parent.mkdir(parents=True)
    probe.write_text("before\n", encoding="utf-8")
    ready = repository_root / ".ai/tasks/ready/TASK-E2E-WRITER-0001.md"
    ready.parent.mkdir(parents=True)
    ready.write_text("# Probe\n\nStatus: READY\n", encoding="utf-8")
    handoff = repository_root / ".ai/handoff"
    handoff.mkdir(parents=True)
    (handoff / "TO-CODEX.md").write_text("ready\n", encoding="utf-8")
    (handoff / "TO-ARCHITECT.md").write_text("waiting\n", encoding="utf-8")
    _git(repository_root, "add", "--", "tests/orchestration/probe.txt", ".ai")
    _git(repository_root, "commit", "-m", "fixture")
    start = _git(repository_root, "rev-parse", "HEAD")
    subprocess.check_call(("git", "init", "--bare", str(remote)))
    _git(repository_root, "remote", "add", "origin", str(remote))
    probe.write_text("after\n", encoding="utf-8")
    inbox = tmp_path / "architect.json"
    inbox.write_text("{}", encoding="utf-8")
    execution = CodexExecutionResult("exec-1", "TASK-E2E-WRITER-0001", start, start,
        ("tests/orchestration/probe.txt",), (ValidationResult("git diff --check", True, "passed"),),
        ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT)
    runner = RunnerResult(RunnerStatus.EXECUTED, execution.task_id, AIDPState.READY_FOR_CODEX,
                          AIDPState.READY_FOR_ARCHITECT, "executed", execution)
    decision = ControlPlaneDecision(ControlPlaneAction.EXECUTE, execution.task_id, AIDPState.READY_FOR_CODEX, "topic", start, "execute")
    control = ControlPlaneResult(decision, ControlPlaneAction.READY_FOR_ARCHITECT, runner_result=runner, architect_inbox_path=str(inbox))
    result = GitReviewPublisher(AIDPRepository(repository_root)).publish(control, "topic")
    assert result.push_status == "PUSHED"
    assert _git(repository_root, "show", "--pretty=", "--name-only", result.execution_commit) == "tests/orchestration/probe.txt"
    projected = set(_git(repository_root, "show", "--pretty=", "--name-only", result.review_envelope_commit).splitlines())
    assert result.review_envelope_path in projected
    assert ".ai/tasks/review/TASK-E2E-WRITER-0001.md" in projected
    assert ".ai/tasks/ready/TASK-E2E-WRITER-0001.md" in projected
    assert not ready.exists()
    envelope = (repository_root / result.review_envelope_path).read_text(encoding="utf-8")
    assert "READY_FOR_ARCHITECT" in envelope and "APPROVED" not in envelope and "prompt" not in envelope.lower()
    assert _git(repository_root, "rev-parse", "refs/remotes/origin/topic") == result.review_envelope_commit


def test_scope_violation_never_commits_or_pushes(tmp_path: Path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "topic")
    _git(root, "config", "user.name", "AIDP Test")
    _git(root, "config", "user.email", "aidp@example.invalid")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", "--", "base.txt")
    _git(root, "commit", "-m", "fixture")
    head = _git(root, "rev-parse", "HEAD")
    inbox = tmp_path / "architect.json"
    inbox.write_text("{}", encoding="utf-8")
    execution = CodexExecutionResult("exec-2", "TASK-E2E-WRITER-0001", head, head, (), (), ExecutionStatus.SCOPE_VIOLATION, "extra file", ScopeCompliance.VIOLATION)
    runner = RunnerResult(RunnerStatus.EXECUTED, execution.task_id, AIDPState.READY_FOR_CODEX, None, "blocked", execution)
    decision = ControlPlaneDecision(ControlPlaneAction.EXECUTE, execution.task_id, AIDPState.READY_FOR_CODEX, "topic", head, "execute")
    control = ControlPlaneResult(decision, ControlPlaneAction.BLOCKED, runner_result=runner, architect_inbox_path=str(inbox))
    result = GitReviewPublisher(AIDPRepository(root)).publish(control, "topic")
    assert result.push_status == "NOT_PUSHED"
    assert _git(root, "rev-parse", "HEAD") == head


def test_exception_after_executing_reaches_terminal_blocked_consumption(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    control = FakeControlPlane()
    control.run_once = lambda: (_ for _ in ()).throw(AssertionError("unexpected control failure"))
    result = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=control,
        publisher=FakePublisher(), runtime_root=runtime, execution_lock_active=lambda: False,
    ).run_once()
    assert result.status is TriggerStatus.BLOCKED
    assert result.consumption_state is ConsumptionState.BLOCKED
    assert ConsumptionStore(runtime).current("contract-1") is ConsumptionState.BLOCKED
    states = [json.loads(line)["consumption_event"]["state"] for line in (runtime / "consumption-events.jsonl").read_text(encoding="utf-8").splitlines()]
    assert states[-2:] == ["EXECUTING", "BLOCKED"]


def test_abandoned_executing_state_is_recovered_as_blocked_without_execution(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    consumption = ConsumptionStore(runtime)
    consumption.append("contract-1", ConsumptionState.RECEIVED, "received")
    consumption.append("contract-1", ConsumptionState.MATERIALIZED, "materialized")
    consumption.append("contract-1", ConsumptionState.EXECUTING, "executing")
    writer, control, publisher = FakeWriter(), FakeControlPlane(), FakePublisher()
    result = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=writer, control_plane=control, publisher=publisher,
        runtime_root=runtime, execution_lock_active=lambda: False,
    ).run_once()
    assert result.status is TriggerStatus.BLOCKED
    assert result.consumption_state is ConsumptionState.BLOCKED
    assert consumption.current("contract-1") is ConsumptionState.BLOCKED
    assert writer.calls == control.calls == publisher.calls == 0


def test_terminal_blocked_item_is_skipped_and_new_contract_remains_eligible(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime, "old-contract")
    (runtime / "contract-inbox/one.json").rename(runtime / "contract-inbox/old-contract.json")
    consumption = ConsumptionStore(runtime)
    consumption.append("old-contract", ConsumptionState.RECEIVED, "received")
    consumption.append("old-contract", ConsumptionState.BLOCKED, "terminal")
    _write_inbox(runtime, "new-contract")
    writer, control, publisher = FakeWriter(), FakeControlPlane(), FakePublisher()
    result = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=writer, control_plane=control, publisher=publisher,
        runtime_root=runtime, execution_lock_active=lambda: False,
    ).run_once()
    assert result.status is TriggerStatus.PUBLISHED
    assert result.contract_id == "new-contract"
    assert consumption.current("old-contract") is ConsumptionState.BLOCKED
    assert consumption.current("new-contract") is ConsumptionState.REVIEW_PUBLISHED


def test_terminal_blocked_only_item_returns_no_action_without_retry(tmp_path: Path):
    runtime = tmp_path / "runtime"
    _write_inbox(runtime)
    consumption = ConsumptionStore(runtime)
    consumption.append("contract-1", ConsumptionState.RECEIVED, "received")
    consumption.append("contract-1", ConsumptionState.BLOCKED, "terminal")
    writer, control, publisher = FakeWriter(), FakeControlPlane(), FakePublisher()
    result = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=writer, control_plane=control, publisher=publisher,
        runtime_root=runtime, execution_lock_active=lambda: False,
    ).run_once()
    assert result.status is TriggerStatus.NO_ACTION
    assert writer.calls == control.calls == publisher.calls == 0


def test_one_authorized_infrastructure_test_failure_retry_is_append_only(tmp_path: Path, monkeypatch) -> None:
    runtime = tmp_path / "runtime"
    _write_inbox(runtime, "infra-retry", "AIDP-INFRA-0002")
    consumption = ConsumptionStore(runtime)
    consumption.append("infra-retry", ConsumptionState.RECEIVED, "received")
    consumption.append("infra-retry", ConsumptionState.MATERIALIZED, "materialized")
    consumption.append("infra-retry", ConsumptionState.EXECUTING, "executing")
    consumption.append("infra-retry", ConsumptionState.BLOCKED, "execution is not review-ready")

    class NoWriter(FakeWriter):
        def materialize_task(self, contract):
            raise AssertionError("recovery must not rematerialize authority")

    watcher = AIDPWatchOnce(
        AIDPRepository(tmp_path, task_namespace="infrastructure"),
        writer=NoWriter(), control_plane=FakeControlPlane(), publisher=FakePublisher(),
        runtime_root=runtime, execution_lock_active=lambda: False,
        allow_test_failure_retry=True,
    )
    monkeypatch.setattr(watcher, "_test_failure_retry_is_authorized", lambda _item: True)
    result = watcher.run_once()
    assert result.status is TriggerStatus.PUBLISHED
    assert [event.state for event in consumption.events("infra-retry")][-3:] == [
        ConsumptionState.RECOVERY_AUTHORIZED,
        ConsumptionState.RECOVERY_EXECUTING,
        ConsumptionState.REVIEW_PUBLISHED,
    ]


def test_blocked_contract_is_not_retried_without_infrastructure_recovery_policy(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    _write_inbox(runtime, "blocked-contract")
    consumption = ConsumptionStore(runtime)
    consumption.append("blocked-contract", ConsumptionState.RECEIVED, "received")
    consumption.append("blocked-contract", ConsumptionState.BLOCKED, "execution is not review-ready")
    watcher = AIDPWatchOnce(
        AIDPRepository(tmp_path), writer=FakeWriter(), control_plane=FakeControlPlane(),
        publisher=FakePublisher(), runtime_root=runtime, execution_lock_active=lambda: False,
    )
    assert watcher.run_once().status is TriggerStatus.NO_ACTION


def test_typed_recovery_authority_binds_residual_and_rejects_replay(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "topic")
    _git(root, "config", "user.name", "AIDP Test")
    _git(root, "config", "user.email", "aidp@example.invalid")
    probe = root / "tests/orchestration/probe.txt"
    probe.parent.mkdir(parents=True)
    probe.write_text("before\n", encoding="utf-8")
    _git(root, "add", "--", "tests/orchestration/probe.txt")
    _git(root, "commit", "-m", "fixture")
    head = _git(root, "rev-parse", "HEAD")
    probe.write_text("after\n", encoding="utf-8")
    runtime_root = tmp_path / "runtime"
    contract = ArchitectTaskContract(
        "AIDP-INFRA-0002", "Recovery", "IMPLEMENTATION", head,
        ("tests/orchestration/probe.txt",), ("no product files",),
        ("git diff --check",), ("recovered",), False, datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    from aidp_orchestration.contracts import ContractInboxItem
    item = ContractInboxItem("authority-contract", contract, datetime(2026, 1, 1, tzinfo=timezone.utc))
    consumption = ConsumptionStore(runtime_root)
    consumption.append(item.contract_id, ConsumptionState.RECEIVED, "received")
    consumption.append(item.contract_id, ConsumptionState.BLOCKED, "terminal")
    digest = GitInspector(root).residual_digest()
    failed = CodexExecutionResult(
        "failed-execution", contract.task_id, head, head,
        ("tests/orchestration/probe.txt",), (), ExecutionStatus.SUPERVISION_FAILED,
        "execution heartbeat persistence failed: OSError", ScopeCompliance.COMPLIANT,
        digest, "pid:7:started_ns:9", True,
    )
    store = LocalRuntimeStore(runtime_root)
    store.persist_result(failed)
    values = dict(
        schema_version="aidp-recovery-authorization-v1", task_id=contract.task_id,
        failed_execution_id=failed.execution_id, terminal_status=failed.status,
        failure_classification=failed.failure_reason, expected_head=head, start_head=head,
        residual_paths=failed.changed_files, residual_digest=digest,
        authorizing_evidence_id=canonical_digest(failed), authorizer_identity=item.contract_id,
        retry_budget=1, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    authority = RecoveryAuthorizationV1(authorization_id=canonical_digest(values), **values)
    store.persist_recovery_authorization(authority)

    class RecoveryRepository:
        task_namespace = "infrastructure"

        def __init__(self): self.root = root
        def inspect(self):
            return OrchestrationDecision(contract.task_id, AIDPState.READY_FOR_CODEX, None,
                                         "topic", head, (), datetime.now(timezone.utc))

    monkeypatch.setattr(LocalRuntimeStore, "for_repository", classmethod(lambda cls, _: store))
    watcher = AIDPWatchOnce(
        RecoveryRepository(), writer=FakeWriter(), control_plane=FakeControlPlane(),
        publisher=FakePublisher(), runtime_root=runtime_root,
        execution_lock_active=lambda: False, allow_test_failure_retry=True,
    )
    assert watcher._typed_recovery_authorization(item) == authority
    store.claim_recovery_authorization(authority.authorization_id, "retry-execution")
    assert watcher._typed_recovery_authorization(item) is None


def test_legacy_one_time_bootstrap_recovery_path_remains_valid(tmp_path: Path, monkeypatch) -> None:
    watcher = AIDPWatchOnce(
        AIDPRepository(tmp_path, task_namespace="infrastructure"),
        writer=FakeWriter(), control_plane=FakeControlPlane(), publisher=FakePublisher(),
        runtime_root=tmp_path / "runtime", execution_lock_active=lambda: False,
        allow_test_failure_retry=True,
    )
    marker = object()
    monkeypatch.setattr(watcher, "_typed_recovery_authorization", lambda _: None)
    monkeypatch.setattr(watcher, "_test_failure_retry_is_authorized", lambda _: False)
    monkeypatch.setattr(watcher, "_abandoned_rework_recovery_is_authorized", lambda item: item is marker)
    assert watcher._recovery_is_authorized(marker)


def _legacy_679_fixture(tmp_path: Path, monkeypatch, *, persist_prior_authority: bool = True):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "topic")
    _git(root, "config", "user.name", "AIDP Test")
    _git(root, "config", "user.email", "aidp@example.invalid")
    paths = (
        "aidp_orchestration/product_owner_http.py",
        "tests/orchestration/test_product_owner_http_security.py",
    )
    for relative in paths:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("before\n", encoding="utf-8")
    _git(root, "add", "--", *paths)
    _git(root, "commit", "-m", "fixture")
    head = _git(root, "rev-parse", "HEAD")
    for relative in paths:
        (root / relative).write_text("after\n", encoding="utf-8")

    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    runtime_root = tmp_path / "runtime"
    store = LocalRuntimeStore(runtime_root)
    finding = ArchitectFinding("F-679", "legacy-recovery", "high", "rework", paths,
                               "recover", "preserve residual")
    prior = create_review_result(
        review_request_id="1" * 64, task_id="AIDP-INFRA-0002", execution_id="prior-execution",
        review_iteration=0, disposition=ArchitectReviewDisposition.FAIL,
        reviewed_head=head, expected_head=head, reviewed_tree_hash="2" * 40,
        findings=(finding,), allowed_rework_scope=paths, required_validations=("pytest",),
        provenance=ArchitectReviewProvenance("architect", "launcher", "model", now, now, "v1"),
        failure_reason=None, authority_claims=(), created_at=now,
    )
    contract = ReworkContract(
        prior.task_id, 1, head, paths,
        (f"{finding.fingerprint}:{finding.rule_id}:{finding.action_id}",), ("pytest",), now,
    )
    contract_id = contract.canonical_id(prior.review_result_id)
    if persist_prior_authority:
        store.persist_architect_result(prior)
        store.append_projection_event(prior.review_result_id, {
            "task_id": prior.task_id, "review_result_id": prior.review_result_id,
            "branch": "topic", "expected_parent": prior.expected_head,
            "projection_commit": head, "disposition": prior.disposition,
            "state": "PUBLISHED", "timestamp": now,
        })
        store.persist_rework_contract(contract_id, contract, prior.review_result_id)

    failed = CodexExecutionResult(
        "679019a9-36f5-457f-b8fa-de4add43d709", contract.task_id, head, None, (), (),
        ExecutionStatus.ERROR, "execution heartbeat persistence failed",
        ScopeCompliance.NOT_EVALUATED, None, None, None,
    )
    store.persist_result(failed)
    attempt = ExecutionAttemptV1(
        schema_version="aidp-execution-attempt-v1", execution_id=failed.execution_id,
        contract_id=contract_id, task_id=contract.task_id, namespace="infrastructure",
        repository_id="repository", expected_head=head, scope_digest=canonical_digest(paths),
        attempt_ordinal=0, retry_budget=0, started_at=now, process_identity=None,
    )
    store.persist_execution_attempt(attempt)
    heartbeat_values = dict(
        schema_version="aidp-execution-heartbeat-v1", execution_id=failed.execution_id,
        sequence=0, observed_at=now, state=ExecutionStatus.RUNNING, previous_digest=None,
    )
    heartbeat = ExecutionHeartbeatV1(
        heartbeat_digest=canonical_digest(heartbeat_values), **heartbeat_values,
    )
    store.persist_execution_heartbeat(heartbeat)
    values = dict(
        schema_version="aidp-legacy-recovery-authorization-v1", task_id=contract.task_id,
        failed_execution_id=failed.execution_id, expected_head=head, start_head=head,
        terminal_result_digest=canonical_digest(failed), execution_attempt_digest=canonical_digest(attempt),
        latest_heartbeat_digest=heartbeat.heartbeat_digest,
        residual_paths=paths, residual_digest=GitInspector(root).residual_digest(),
        prior_rework_authority_id=prior.review_result_id, authorizer_identity=contract_id,
        retry_budget=1, created_at=now,
    )
    authority = LegacyRecoveryAuthorizationV1(authorization_id=canonical_digest(values), **values)
    from aidp_orchestration.contracts import ContractInboxItem
    item = ContractInboxItem(contract_id, contract, now)
    consumption = ConsumptionStore(runtime_root)
    consumption.append(contract_id, ConsumptionState.RECEIVED, "received")
    consumption.append(contract_id, ConsumptionState.BLOCKED, "terminal")

    class RecoveryRepository:
        task_namespace = "infrastructure"

        def __init__(self): self.root = root
        def inspect(self):
            return OrchestrationDecision(contract.task_id, AIDPState.REWORK_REQUIRED, None,
                                         "topic", head, (), now)

    monkeypatch.setattr(LocalRuntimeStore, "for_repository", classmethod(lambda cls, _: store))
    watcher = AIDPWatchOnce(
        RecoveryRepository(), writer=FakeWriter(), control_plane=FakeControlPlane(),
        publisher=FakePublisher(), runtime_root=runtime_root,
        execution_lock_active=lambda: False, allow_test_failure_retry=True,
    )
    return watcher, item, store, authority, values


def test_legacy_679_recovery_requires_exact_typed_authority_and_rejects_replay(tmp_path, monkeypatch) -> None:
    watcher, item, store, authority, _ = _legacy_679_fixture(tmp_path, monkeypatch)
    store.persist_recovery_authorization(authority)
    assert watcher._typed_recovery_authorization(item) == authority
    store.claim_recovery_authorization(authority.authorization_id, "retry-execution")
    assert watcher._typed_recovery_authorization(item) is None


def test_legacy_679_recovery_does_not_require_supervision_failure(tmp_path, monkeypatch) -> None:
    watcher, item, store, authority, _ = _legacy_679_fixture(tmp_path, monkeypatch)
    assert not (store.root / "execution-supervision-failures").exists()
    store.persist_recovery_authorization(authority)
    assert watcher._typed_recovery_authorization(item) == authority


def test_fake_supervision_failure_cannot_substitute_for_missing_historical_evidence(tmp_path, monkeypatch) -> None:
    watcher, item, store, authority, _ = _legacy_679_fixture(tmp_path, monkeypatch)
    (store.root / "execution-heartbeats" / f"{authority.failed_execution_id}.json").unlink()
    failure_values = dict(
        schema_version="aidp-execution-supervision-failure-v1",
        execution_id=authority.failed_execution_id, exception_class="OSError",
        observed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    store.persist_supervision_failure(ExecutionSupervisionFailureV1(
        failure_id=canonical_digest(failure_values), **failure_values,
    ))
    store.persist_recovery_authorization(authority)
    assert watcher._typed_recovery_authorization(item) is None


@pytest.mark.parametrize("mismatch", (
    "task", "path", "digest", "head", "execution", "result_identity", "attempt", "heartbeat",
    "missing_prior_authority",
))
def test_legacy_679_recovery_rejects_mismatched_or_unbound_authority(
    tmp_path, monkeypatch, mismatch,
) -> None:
    watcher, item, store, _, values = _legacy_679_fixture(
        tmp_path, monkeypatch, persist_prior_authority=mismatch != "missing_prior_authority",
    )
    if mismatch == "task": values["task_id"] = "AIDP-INFRA-9999"
    elif mismatch == "path": values["residual_paths"] = ("other.py",)
    elif mismatch == "digest": values["residual_digest"] = "3" * 64
    elif mismatch == "head": values["expected_head"] = "4" * 40
    elif mismatch == "execution": values["failed_execution_id"] = "wrong-execution"
    elif mismatch == "result_identity": values["terminal_result_digest"] = "5" * 64
    elif mismatch == "attempt": values["execution_attempt_digest"] = "6" * 64
    elif mismatch == "heartbeat": values["latest_heartbeat_digest"] = "7" * 64
    authority = LegacyRecoveryAuthorizationV1(authorization_id=canonical_digest(values), **values)
    store.persist_recovery_authorization(authority)
    assert watcher._typed_recovery_authorization(item) is None


@pytest.mark.parametrize("missing", (
    "attempt", "heartbeat", "result", "architect_result", "rework_contract",
))
def test_legacy_679_recovery_rejects_missing_historical_evidence(
    tmp_path, monkeypatch, missing,
) -> None:
    watcher, item, store, authority, _ = _legacy_679_fixture(tmp_path, monkeypatch)
    if missing == "attempt":
        (store.root / "execution-attempts" / f"{authority.failed_execution_id}.json").unlink()
    elif missing == "heartbeat":
        (store.root / "execution-heartbeats" / f"{authority.failed_execution_id}.json").unlink()
    elif missing == "result":
        (store.root / "results" / f"{authority.failed_execution_id}.json").unlink()
    elif missing == "architect_result":
        (store.root / "architect-review-results" / f"{authority.prior_rework_authority_id}.json").unlink()
    elif missing == "rework_contract":
        next((store.root / "rework-contracts" / item.contract.task_id).glob("*.json")).unlink()
    store.persist_recovery_authorization(authority)
    assert watcher._typed_recovery_authorization(item) is None
