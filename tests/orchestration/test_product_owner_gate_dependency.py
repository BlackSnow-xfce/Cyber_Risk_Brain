from __future__ import annotations

import json
import subprocess
import threading
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from aidp_orchestration.contracts import (
    ArchitectReviewDisposition, ArchitectReviewProvenance, CodexExecutionResult, ContractInboxItem,
    ExecutionStatus, ProductOwnerGateDependencyAuthorityV1, ProductOwnerGateDependencyState,
    ScopeCompliance, ValidationResult, canonical_digest, utc_now,
)
from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.runner import AIDPRunner
from aidp_orchestration.trigger_publisher import (
    LocalContractInbox, ProductOwnerGateDependencyRunner, serialize_contract_inbox_item,
)


def authority(**overrides) -> ProductOwnerGateDependencyAuthorityV1:
    issued = utc_now()
    values = dict(
        schema_version="aidp-product-owner-gate-dependency-authority-v1",
        parent_task_id="AIDP-INFRA-0002", dependency_id="AIDP-PO-DEP-0002",
        purpose=ProductOwnerGateDependencyAuthorityV1.PURPOSE,
        repository_id="1" * 64, git_common_id="3" * 64, repository_remote_id="4" * 64,
        branch="aidp/infrastructure-lifecycle",
        expected_head="2" * 40,
        allowed_scope=("aidp_orchestration/product_owner_deployment.py", "tests/orchestration/test_product_owner_deployment.py"),
        prohibited_actions=(".ai/**", "accept parent task"),
        validation_requirements=("python -m pytest tests/orchestration", "git diff --check"),
        acceptance_criteria=("Deploy confirmation boundary only", "Do not mutate parent lifecycle"),
        issued_by="Product Owner bootstrap", issued_at=issued, expires_at=issued + timedelta(days=2),
    )
    values.update(overrides)
    identifier = canonical_digest(values)
    return ProductOwnerGateDependencyAuthorityV1(authority_id=identifier, **values)


def test_closed_schema_and_canonical_identity() -> None:
    value = authority()
    item = ContractInboxItem(value.authority_id, value, utc_now())
    encoded = serialize_contract_inbox_item(item)
    assert LocalContractInbox.parse(encoded.encode()).contract == item.contract
    payload = json.loads(encoded)
    payload["contract_inbox_item"]["contract"]["purpose"] = "EXECUTE_AIDP_INFRA_0005"
    with pytest.raises(ValueError):
        LocalContractInbox.parse(json.dumps(payload).encode())
    payload = json.loads(encoded)
    payload["contract_inbox_item"]["contract"]["unknown"] = True
    with pytest.raises(ValueError):
        LocalContractInbox.parse(json.dumps(payload).encode())


@pytest.mark.parametrize("field,value", [
    ("parent_task_id", "AIDP-INFRA-0005"),
    ("dependency_id", "AIDP-INFRA-0005"),
    ("purpose", "GENERAL_CONCURRENT_INFRASTRUCTURE"),
    ("expected_head", "bad"),
    ("schema_version", "v2"),
])
def test_invalid_or_tampered_authority_is_rejected(field: str, value: str) -> None:
    original = authority()
    with pytest.raises(ValueError):
        replace(original, **{field: value})


def test_dependency_id_is_not_valid_ordinary_task_authority() -> None:
    from aidp_orchestration.contracts import ArchitectTaskContract

    with pytest.raises(ValueError):
        ArchitectTaskContract(
            task_id="AIDP-PO-DEP-0002", title="x", phase="x",
            expected_head="2" * 40, allowed_scope=("a",), prohibited_actions=("b",),
            acceptance_criteria=("c",), validation_requirements=("pytest",),
            product_owner_gate=True, created_at=utc_now(),
        )


@pytest.mark.parametrize("path", [
    ".ai/tasks/review/AIDP-INFRA-0002.md", ".git/config",
    "aidp_orchestration/contracts.py", "aidp_orchestration/runtime.py",
    "aidp_orchestration/product_owner_confirmation.py", "aidp_orchestration/lifecycle.py",
    "aidp_orchestration/unrelated.py", "tests/orchestration/test_unrelated.py",
])
def test_canonical_authority_rejects_protected_or_unrelated_scope(path: str) -> None:
    with pytest.raises(ValueError):
        authority(allowed_scope=(path,))


def test_claim_is_durable_single_use_and_concurrent(tmp_path: Path) -> None:
    store = LocalRuntimeStore(tmp_path)
    value = authority()
    outcomes: list[str] = []

    def claim() -> None:
        try:
            store.claim_product_owner_gate_dependency(value, "execution-1")
            outcomes.append("claimed")
        except RuntimeError:
            outcomes.append("blocked")

    threads = [threading.Thread(target=claim) for _ in range(2)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    assert sorted(outcomes) == ["blocked", "claimed"]
    assert store.product_owner_gate_dependency_claimed(value.authority_id)
    with pytest.raises(RuntimeError):
        LocalRuntimeStore(tmp_path).claim_product_owner_gate_dependency(value, "execution-2")


def test_authority_cannot_claim_parent_acceptance_or_decision_journal(tmp_path: Path) -> None:
    store = LocalRuntimeStore(tmp_path)
    value = authority()
    store.claim_product_owner_gate_dependency(value, "execution-1")
    assert not (tmp_path / "product-owner-decisions").exists()
    assert not (tmp_path / "approval-contexts").exists()
    assert not (tmp_path / "decision-journal").exists()


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _repository(tmp_path: Path) -> tuple[Path, Path]:
    root, remote = tmp_path / "infra", tmp_path / "origin.git"
    subprocess.check_call(("git", "init", "--bare", str(remote)))
    root.mkdir()
    _git(root, "init", "-b", "aidp/infrastructure-lifecycle")
    _git(root, "config", "user.name", "AIDP Test")
    _git(root, "config", "user.email", "aidp@example.invalid")
    _git(root, "remote", "add", "origin", str(remote))
    task = root / ".ai/tasks/review/AIDP-INFRA-0002.md"
    task.parent.mkdir(parents=True)
    task.write_text(
        "---\ntask_id: AIDP-INFRA-0002\nphase: IMPLEMENTATION\n"
        "allowed_scope: aidp_orchestration/**\nprohibited_actions: .ai/**\n"
        "validation_requirements: pytest\nproduct_owner_gate: true\n---\n"
        "Status: ARCHITECT_APPROVED\n", encoding="utf-8",
    )
    handoff = root / ".ai/handoff"
    handoff.mkdir(parents=True)
    (handoff / "TO-CODEX.md").write_text("status: CLOSED\ntask_id: AIDP-INFRA-0002\n", encoding="utf-8")
    (handoff / "TO-ARCHITECT.md").write_text("status: CLOSED\ntask_id: AIDP-INFRA-0002\n", encoding="utf-8")
    target = root / "aidp_orchestration/product_owner_http.py"
    target.parent.mkdir(parents=True)
    target.write_text("INITIAL = True\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "fixture")
    _git(root, "push", "-u", "origin", "aidp/infrastructure-lifecycle")
    return root, remote


def _bound_authority(root: Path, **overrides) -> ProductOwnerGateDependencyAuthorityV1:
    common = Path(_git(root, "rev-parse", "--git-common-dir"))
    common = (root / common).resolve() if not common.is_absolute() else common.resolve()
    values = dict(
        repository_id=canonical_digest(str(root.resolve()).lower()),
        git_common_id=canonical_digest(str(common).lower()),
        repository_remote_id=canonical_digest(_git(root, "remote", "get-url", "origin")),
        expected_head=_git(root, "rev-parse", "HEAD"),
        allowed_scope=("aidp_orchestration/product_owner_http.py",),
    )
    values.update(overrides)
    return authority(**values)


def test_runner_uses_isolated_branch_and_preserves_waiting_parent(tmp_path: Path, monkeypatch) -> None:
    root, _remote = _repository(tmp_path)
    monkeypatch.setattr("aidp_orchestration.trigger_publisher.tempfile.gettempdir", lambda: str(tmp_path / "absent-runtime-temp"))
    runtime_root = tmp_path / "shared-runtime"
    value = _bound_authority(root)
    LocalContractInbox(runtime_root).persist(ContractInboxItem(value.authority_id, value, utc_now()))
    before = (_git(root, "rev-parse", "HEAD"), _git(root, "branch", "--show-current"),
              (root / ".ai/tasks/review/AIDP-INFRA-0002.md").read_bytes(),
              (root / ".ai/handoff/TO-CODEX.md").read_bytes(),
              (root / ".ai/handoff/TO-ARCHITECT.md").read_bytes())

    class FakeExecutionRunner:
        def __init__(self, repository, *, timeout_seconds): self.repository = repository
        def execute_authorized(self, request, *, contract_id, namespace):
            assert contract_id == value.authority_id
            assert namespace == "product-owner-gate-dependency"
            assert request.branch.startswith("aidp/gate-dependency-")
            path = Path(request.repository) / "aidp_orchestration/product_owner_http.py"
            path.write_text("INITIAL = True\nDEPLOYED = True\n", encoding="utf-8")
            return CodexExecutionResult(
                request.execution_id, request.task_id, request.expected_head, request.expected_head,
                ("aidp_orchestration/product_owner_http.py",),
                (ValidationResult("python -m pytest tests/orchestration", True, "pass"),
                 ValidationResult("git diff --check", True, "pass")),
                ExecutionStatus.SUCCESS, None, ScopeCompliance.COMPLIANT,
            )

    class Guard:
        def __init__(self, workspace): self.workspace = workspace
        def validate(self, *, expected_head=None, require_clean=True):
            assert _git(self.workspace, "rev-parse", "HEAD") == expected_head
            common = Path(_git(self.workspace, "rev-parse", "--git-common-dir"))
            common = (self.workspace / common).resolve() if not common.is_absolute() else common.resolve()
            return {"repository": str(self.workspace.resolve()), "git_common_dir": str(common),
                    "branch": _git(self.workspace, "branch", "--show-current"),
                    "remote_url": _git(self.workspace, "remote", "get-url", "origin"), "head": expected_head}

    class Architect:
        def __init__(self, workspace): self.identity_guard = Guard(workspace)
        def review(self, request, *, schema_path):
            provenance = ArchitectReviewProvenance("process", "launcher", "model", utc_now(), utc_now(), "architect-review-result-v1")
            return create_review_result(
                review_request_id=request.review_request_id, task_id=request.task_id,
                execution_id=request.execution_id, review_iteration=0,
                disposition=ArchitectReviewDisposition.PASS, reviewed_head=request.reviewed_head,
                expected_head=request.expected_current_head, reviewed_tree_hash=request.reviewed_tree_hash,
                findings=(), allowed_rework_scope=(), required_validations=(), provenance=provenance,
                failure_reason=None, authority_claims=(), created_at=utc_now(),
            )
        def revalidate(self, request): self.identity_guard.validate(expected_head=request.expected_current_head)

    monkeypatch.setattr("aidp_orchestration.trigger_publisher.AIDPRunner", FakeExecutionRunner)
    shell_architect = type("Shell", (), {})()
    runner = ProductOwnerGateDependencyRunner(
        AIDPRepository(root, task_namespace="infrastructure"), runtime_root=runtime_root,
        architect=shell_architect,
    )
    monkeypatch.setattr(runner, "_workspace_architect", lambda workspace, branch: Architect(workspace))
    result = runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED_PENDING_PROVISIONING
    after = (_git(root, "rev-parse", "HEAD"), _git(root, "branch", "--show-current"),
             (root / ".ai/tasks/review/AIDP-INFRA-0002.md").read_bytes(),
             (root / ".ai/handoff/TO-CODEX.md").read_bytes(),
             (root / ".ai/handoff/TO-ARCHITECT.md").read_bytes())
    assert after == before
    assert _git(root, "status", "--porcelain=v1") == ""
    assert AIDPRepository(root, task_namespace="infrastructure").inspect().state.value == "WAITING_FOR_PRODUCT_OWNER"
    replay = runner.run_once()
    assert replay.state is ProductOwnerGateDependencyState.BLOCKED


def test_stale_authority_blocks_before_workspace_or_child(tmp_path: Path, monkeypatch) -> None:
    root, _remote = _repository(tmp_path)
    runtime_root = tmp_path / "shared-runtime"
    value = _bound_authority(root, expected_head="f" * 40)
    LocalContractInbox(runtime_root).persist(ContractInboxItem(value.authority_id, value, utc_now()))
    monkeypatch.setattr("aidp_orchestration.trigger_publisher.AIDPRunner", lambda *a, **k: pytest.fail("child launched"))
    runner = ProductOwnerGateDependencyRunner(
        AIDPRepository(root, task_namespace="infrastructure"), runtime_root=runtime_root,
        architect=object(),
    )
    result = runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert not LocalRuntimeStore.for_repository(root).product_owner_gate_dependency_claimed(value.authority_id)


def test_dependency_execution_uses_durable_attempt_and_heartbeat_supervision(tmp_path: Path) -> None:
    root, _remote = _repository(tmp_path)
    store = LocalRuntimeStore(tmp_path / "runtime")
    from aidp_orchestration.contracts import CodexExecutionRequest
    execution_request = CodexExecutionRequest(
        "AIDP-PO-DEP-0002", root / ".ai/tasks/review/AIDP-INFRA-0002.md", str(root),
        "aidp/infrastructure-lifecycle", _git(root, "rev-parse", "HEAD"),
        _git(root, "rev-parse", "HEAD"), "PRODUCT_OWNER_GATE_DEPENDENCY",
        ("aidp_orchestration/product_owner_http.py",), (".ai/**",),
        ("pytest",), utc_now(), "dependency-execution-1", 0, ("criterion",),
    )

    class Service:
        def execute(self, request, supervision_event=None):
            assert supervision_event is not None
            return CodexExecutionResult(
                request.execution_id, request.task_id, request.expected_head, request.expected_head,
                ("aidp_orchestration/product_owner_http.py",),
                (ValidationResult("pytest", True, "pass"),), ExecutionStatus.SUCCESS, None,
                ScopeCompliance.COMPLIANT,
            )

    runner = AIDPRunner(
        AIDPRepository(root, task_namespace="infrastructure"),
        execution_service=Service(), runtime_store=store,
    )
    result = runner.execute_authorized(
        execution_request, contract_id="a" * 64, namespace="product-owner-gate-dependency",
    )
    assert result.status is ExecutionStatus.SUCCESS
    attempt = store.execution_attempt(execution_request.execution_id)
    assert attempt.contract_id == "a" * 64
    assert attempt.namespace == "product-owner-gate-dependency"
    assert attempt.expected_head == execution_request.expected_head
    assert attempt.scope_digest == canonical_digest({
        "allowed": execution_request.allowed_scope,
        "prohibited": execution_request.prohibited_actions,
    })
    assert store.execution_heartbeat(execution_request.execution_id) is not None


@pytest.mark.parametrize("mutation", ["branch", "git_common_id", "repository_remote_id", "expires_at"])
def test_repository_authority_substitution_blocks_before_claim(tmp_path: Path, mutation: str) -> None:
    root, _remote = _repository(tmp_path)
    value = _bound_authority(root)
    replacement = {
        "branch": "wrong",
        "git_common_id": "b" * 64,
        "repository_remote_id": "c" * 64,
        "expires_at": utc_now() - timedelta(days=1),
    }[mutation]
    values = {
        "repository_id": value.repository_id, "git_common_id": value.git_common_id,
        "repository_remote_id": value.repository_remote_id, "branch": value.branch,
        "expected_head": value.expected_head, "allowed_scope": value.allowed_scope,
        mutation: replacement,
    }
    if mutation == "expires_at": values["issued_at"] = utc_now() - timedelta(days=2)
    value = authority(**values)
    runner = ProductOwnerGateDependencyRunner(
        AIDPRepository(root, task_namespace="infrastructure"), runtime_root=tmp_path / "runtime",
        architect=object(),
    )
    with pytest.raises(ValueError): runner._validate(value)


def test_ambiguous_unclaimed_authorities_block_without_claim(tmp_path: Path) -> None:
    root, _remote = _repository(tmp_path)
    runtime = tmp_path / "runtime"
    first = _bound_authority(root)
    second = _bound_authority(root, dependency_id="AIDP-PO-DEP-0003")
    inbox = LocalContractInbox(runtime)
    inbox.persist(ContractInboxItem(first.authority_id, first, utc_now()))
    inbox.persist(ContractInboxItem(second.authority_id, second, utc_now()))
    runner = ProductOwnerGateDependencyRunner(
        AIDPRepository(root, task_namespace="infrastructure"), runtime_root=runtime,
        architect=object(),
    )
    result = runner.run_once()
    assert result.state is ProductOwnerGateDependencyState.BLOCKED
    assert not runner.store.product_owner_gate_dependency_claimed(first.authority_id)
    assert not runner.store.product_owner_gate_dependency_claimed(second.authority_id)
