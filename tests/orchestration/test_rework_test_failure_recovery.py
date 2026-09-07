from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from aidp_orchestration.contracts import (
    AIDPState,
    CodexExecutionResult,
    ConsumptionState,
    ExecutionStatus,
    ReworkContract,
    ScopeCompliance,
    ValidationResult,
)
from aidp_orchestration.trigger_publisher import AIDPWatchOnce, ConsumptionStore
import aidp_orchestration.trigger_publisher as trigger_publisher


class _UnusedBoundary:
    def __getattr__(self, name):
        raise AssertionError(f"unexpected boundary call: {name}")


class _Repository:
    task_namespace = "infrastructure"

    def __init__(self, root, *, task_id: str, head: str):
        self.root = root
        self.task_id = task_id
        self.head = head

    def inspect(self):
        return SimpleNamespace(
            state=AIDPState.REWORK_REQUIRED,
            task_id=self.task_id,
            commit=self.head,
        )

    def build_execution_request(self, task_id: str, *, rework_count: int = 0):
        assert task_id == self.task_id
        assert rework_count == 3
        return object()

    def validate_scope(self, request, changed_files):
        return ScopeCompliance.COMPLIANT


class _Runtime:
    def __init__(self, result):
        self.result = result

    def latest_execution_result(self, task_id: str):
        assert task_id == self.result.task_id
        return self.result

    def recovery_authorizations(self):
        return ()


class _Inspector:
    def __init__(self, changed_files):
        self._changed_files = changed_files

    def changed_files(self):
        return self._changed_files

    def residual_digest(self):
        return None


def _watcher(tmp_path, monkeypatch):
    task_id = "AIDP-INFRA-0002"
    head = "a" * 40
    contract = ReworkContract(
        task_id=task_id,
        review_iteration=3,
        expected_head=head,
        allowed_rework_scope=("aidp_orchestration/product_owner_http.py",),
        findings=("finding",),
        required_validations=("python -m pytest tests/orchestration", "git diff --check"),
        created_at=datetime(2026, 9, 7, tzinfo=timezone.utc),
    )
    result = CodexExecutionResult(
        execution_id="exec-test-failed",
        task_id=task_id,
        start_commit=head,
        resulting_commit=head,
        changed_files=(),
        validation_results=(
            ValidationResult("python -m pytest tests/orchestration", False, "exit_code=1"),
            ValidationResult("git diff --check", True, "passed"),
        ),
        status=ExecutionStatus.TEST_FAILED,
        failure_reason="one or more validations failed",
        scope_compliance=ScopeCompliance.COMPLIANT,
    )
    repository = _Repository(tmp_path, task_id=task_id, head=head)
    runtime = tmp_path / "runtime"
    watcher = AIDPWatchOnce(
        repository,
        writer=_UnusedBoundary(),
        control_plane=_UnusedBoundary(),
        publisher=_UnusedBoundary(),
        runtime_root=runtime,
        execution_lock_active=lambda: False,
        allow_test_failure_retry=True,
    )
    consumption = ConsumptionStore(runtime)
    consumption.append("rework-contract", ConsumptionState.RECEIVED, "received")
    consumption.append("rework-contract", ConsumptionState.MATERIALIZED, "materialized")
    consumption.append("rework-contract", ConsumptionState.EXECUTING, "executing")
    consumption.append("rework-contract", ConsumptionState.BLOCKED, "execution is not review-ready")
    monkeypatch.setattr(
        trigger_publisher.LocalRuntimeStore,
        "for_repository",
        staticmethod(lambda _root: _Runtime(result)),
    )
    monkeypatch.setattr(
        trigger_publisher,
        "GitInspector",
        lambda _root: _Inspector(result.changed_files),
    )
    item = SimpleNamespace(contract_id="rework-contract", contract=contract)
    return watcher, consumption, item


def test_rework_test_failure_is_eligible_for_one_bounded_recovery(tmp_path, monkeypatch):
    watcher, _consumption, item = _watcher(tmp_path, monkeypatch)
    assert watcher._rework_test_failure_retry_is_authorized(item) is True
    assert watcher._recovery_is_authorized(item) is True


def test_rework_test_failure_retry_is_rejected_after_recovery_was_already_authorized(tmp_path, monkeypatch):
    watcher, consumption, item = _watcher(tmp_path, monkeypatch)
    consumption.append(
        "rework-contract",
        ConsumptionState.RECOVERY_AUTHORIZED,
        "one bounded infrastructure recovery authorized",
    )
    assert watcher._rework_test_failure_retry_is_authorized(item) is False
