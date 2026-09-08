"""Fail-closed recovery and deterministic successor arbitration for Product Owner gate dependency bootstrap."""

from __future__ import annotations

import subprocess
from dataclasses import fields
from pathlib import Path

from .contracts import ProductOwnerGateDependencyAuthorityV1, ProductOwnerGateDependencyResult
from .trigger_publisher import ProductOwnerGateDependencyRunner


class _BootstrapRecoveryStoreProxy:
    def __init__(self, store, authority_id: str):
        self._store = store
        self._authority_id = authority_id

    def product_owner_gate_dependency_claimed(self, authority_id: str) -> bool:
        if authority_id == self._authority_id:
            return False
        return self._store.product_owner_gate_dependency_claimed(authority_id)

    def claim_product_owner_gate_dependency(self, authority, execution_id: str):
        if authority.authority_id != self._authority_id:
            return self._store.claim_product_owner_gate_dependency(authority, execution_id)
        path = self._store.root / "product-owner-gate-dependency-claims" / f"{authority.authority_id}.json"
        if not path.is_file():
            raise RuntimeError("gate dependency recovery claim disappeared")
        return path

    def __getattr__(self, name):
        return getattr(self._store, name)


class _SelectedAuthorityInboxProxy:
    def __init__(self, inbox, authority_id: str):
        self._inbox = inbox
        self._authority_id = authority_id

    def pending(self):
        values = []
        for item in self._inbox.pending():
            if isinstance(item.contract, ProductOwnerGateDependencyAuthorityV1):
                if item.contract_id == self._authority_id:
                    values.append(item)
                continue
            values.append(item)
        return tuple(values)

    def __getattr__(self, name):
        return getattr(self._inbox, name)


class RecoveringProductOwnerGateDependencyRunner(ProductOwnerGateDependencyRunner):
    """Resume orphaned bootstrap work and arbitrate equivalent immutable successor authorities."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._recovering_authority_id: str | None = None

    def run_once(self) -> ProductOwnerGateDependencyResult:
        all_candidates = tuple(
            item
            for item in self.inbox.pending()
            if isinstance(item.contract, ProductOwnerGateDependencyAuthorityV1)
        )
        claimed = tuple(
            item
            for item in all_candidates
            if self.store.product_owner_gate_dependency_claimed(item.contract_id)
        )
        if len(claimed) == 1 and self._bootstrap_recovery_authorized(claimed[0].contract):
            authority = claimed[0].contract
            original_store = self.store
            self._recovering_authority_id = authority.authority_id
            self.store = _BootstrapRecoveryStoreProxy(original_store, authority.authority_id)
            try:
                return super().run_once()
            finally:
                self.store = original_store
                self._recovering_authority_id = None

        if claimed:
            return super().run_once()

        selected = self._equivalent_successor(all_candidates)
        if selected is None:
            return super().run_once()
        original_inbox = self.inbox
        self.inbox = _SelectedAuthorityInboxProxy(original_inbox, selected.contract_id)
        try:
            return super().run_once()
        finally:
            self.inbox = original_inbox

    @staticmethod
    def _equivalent_successor(items):
        if len(items) < 2:
            return None
        ignored = {"authority_id", "issued_at", "expires_at"}

        def semantic_values(contract):
            return tuple(
                (field.name, getattr(contract, field.name))
                for field in fields(contract)
                if field.name not in ignored
            )

        first = semantic_values(items[0].contract)
        if any(semantic_values(item.contract) != first for item in items[1:]):
            return None
        ordered = sorted(items, key=lambda item: item.contract.issued_at)
        if ordered[-1].contract.issued_at == ordered[-2].contract.issued_at:
            return None
        return ordered[-1]

    def _bootstrap_recovery_authorized(self, authority: ProductOwnerGateDependencyAuthorityV1) -> bool:
        try:
            self._validate(authority)
            workspace = self._workspace_path(authority)
            if workspace.exists():
                return False
            branch = self._dependency_branch(authority)
            if not self._local_branch_exists(branch):
                return False
            if self._git_at(self.repository.root, "rev-parse", branch) != authority.expected_head:
                return False
            if self._branch_has_worktree(branch):
                return False
            remote_ref = f"refs/remotes/origin/{branch}"
            if self._ref_exists(remote_ref):
                if self._git_at(self.repository.root, "rev-parse", remote_ref) != authority.expected_head:
                    return False
            return True
        except (OSError, RuntimeError, ValueError, subprocess.SubprocessError):
            return False

    def _prepare_workspace(self, authority: ProductOwnerGateDependencyAuthorityV1) -> tuple[Path, str]:
        if self._recovering_authority_id != authority.authority_id:
            return super()._prepare_workspace(authority)
        workspace = self._workspace_path(authority)
        if workspace.exists():
            raise RuntimeError("gate dependency recovery workspace already exists")
        workspace.parent.mkdir(parents=True, exist_ok=True)
        branch = self._dependency_branch(authority)
        if not self._local_branch_exists(branch):
            raise RuntimeError("gate dependency recovery branch is missing")
        if self._git_at(self.repository.root, "rev-parse", branch) != authority.expected_head:
            raise RuntimeError("gate dependency recovery branch diverged")
        if self._branch_has_worktree(branch):
            raise RuntimeError("gate dependency recovery branch is already attached")
        self._git_at(self.repository.root, "worktree", "add", str(workspace), branch)
        self._git_at(workspace, "push", "-u", "origin", branch)
        return workspace, branch

    @staticmethod
    def _workspace_path(authority: ProductOwnerGateDependencyAuthorityV1) -> Path:
        import tempfile

        return Path(tempfile.gettempdir()).resolve() / f"aidp-gate-dependency-{authority.authority_id[:12]}"

    @staticmethod
    def _dependency_branch(authority: ProductOwnerGateDependencyAuthorityV1) -> str:
        return f"aidp/gate-dependency-{authority.authority_id[:12]}"

    def _local_branch_exists(self, branch: str) -> bool:
        return self._ref_exists(f"refs/heads/{branch}")

    def _ref_exists(self, ref: str) -> bool:
        return subprocess.run(
            ("git", "show-ref", "--verify", "--quiet", ref),
            cwd=self.repository.root,
            check=False,
        ).returncode == 0

    def _branch_has_worktree(self, branch: str) -> bool:
        output = self._git_at(self.repository.root, "worktree", "list", "--porcelain")
        return f"branch refs/heads/{branch}" in output.splitlines()
