from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

from aidp_orchestration.contracts import ProductOwnerGateDependencyResult, ProductOwnerGateDependencyState
from aidp_orchestration.gate_dependency_recovery import RecoveringProductOwnerGateDependencyRunner
from aidp_orchestration.trigger_publisher import ProductOwnerGateDependencyRunner


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True, stderr=subprocess.STDOUT).strip()


def _repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-b", "aidp/infrastructure-lifecycle")
    _git(root, "config", "user.name", "AIDP Test")
    _git(root, "config", "user.email", "aidp@example.invalid")
    (root / "marker.txt").write_text("base\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-m", "base")
    return root, _git(root, "rev-parse", "HEAD")


def test_orphaned_claim_branch_is_recoverable_only_at_expected_head(tmp_path: Path, monkeypatch) -> None:
    root, head = _repo(tmp_path)
    authority = SimpleNamespace(authority_id="a" * 64, expected_head=head)
    branch = f"aidp/gate-dependency-{authority.authority_id[:12]}"
    _git(root, "branch", branch, head)

    runner = object.__new__(RecoveringProductOwnerGateDependencyRunner)
    runner.repository = SimpleNamespace(root=root)
    monkeypatch.setattr(runner, "_validate", lambda value: None)
    monkeypatch.setattr(runner, "_workspace_path", lambda value: tmp_path / "missing-workspace")

    assert runner._bootstrap_recovery_authorized(authority)

    _git(root, "checkout", branch)
    (root / "marker.txt").write_text("diverged\n", encoding="utf-8")
    _git(root, "commit", "-am", "diverge")
    _git(root, "checkout", "aidp/infrastructure-lifecycle")

    assert not runner._bootstrap_recovery_authorized(authority)


def test_claimed_orphan_uses_proxy_without_replaying_claim(tmp_path: Path, monkeypatch) -> None:
    authority = SimpleNamespace(authority_id="b" * 64, dependency_id="AIDP-PO-DEP-0002")
    item = SimpleNamespace(contract_id=authority.authority_id, contract=authority)
    monkeypatch.setattr(
        "aidp_orchestration.gate_dependency_recovery.ProductOwnerGateDependencyAuthorityV1",
        SimpleNamespace,
    )

    class Inbox:
        def pending(self):
            return (item,)

    class Store:
        def __init__(self):
            self.root = tmp_path / "runtime"
            claim = self.root / "product-owner-gate-dependency-claims" / f"{authority.authority_id}.json"
            claim.parent.mkdir(parents=True)
            claim.write_text("{}\n", encoding="utf-8")

        def product_owner_gate_dependency_claimed(self, authority_id: str) -> bool:
            return authority_id == authority.authority_id

    runner = object.__new__(RecoveringProductOwnerGateDependencyRunner)
    runner.inbox = Inbox()
    runner.store = Store()
    runner._recovering_authority_id = None
    monkeypatch.setattr(runner, "_bootstrap_recovery_authorized", lambda value: True)

    def fake_base_run_once(self):
        assert not self.store.product_owner_gate_dependency_claimed(authority.authority_id)
        self.store.claim_product_owner_gate_dependency(authority, "recovery-execution")
        return ProductOwnerGateDependencyResult(
            authority.authority_id,
            authority.dependency_id,
            ProductOwnerGateDependencyState.EXECUTING,
            "recovery-execution",
        )

    monkeypatch.setattr(ProductOwnerGateDependencyRunner, "run_once", fake_base_run_once)

    result = RecoveringProductOwnerGateDependencyRunner.run_once(runner)

    assert result.state is ProductOwnerGateDependencyState.EXECUTING
    assert runner.store.product_owner_gate_dependency_claimed(authority.authority_id)
    assert runner._recovering_authority_id is None
