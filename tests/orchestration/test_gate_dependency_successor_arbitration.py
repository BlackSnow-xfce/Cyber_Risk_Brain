from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from types import SimpleNamespace

from aidp_orchestration.gate_dependency_recovery import RecoveringProductOwnerGateDependencyRunner


@dataclass(frozen=True)
class FakeAuthority:
    authority_id: str
    parent_task_id: str
    dependency_id: str
    purpose: str
    expected_head: str
    allowed_scope: tuple[str, ...]
    issued_at: datetime
    expires_at: datetime


def _item(identifier: str, issued_hour: int, *, scope: tuple[str, ...] = ("a",)):
    authority = FakeAuthority(
        authority_id=identifier,
        parent_task_id="AIDP-INFRA-0002",
        dependency_id="AIDP-PO-DEP-0002",
        purpose="DEPLOY_PRODUCT_OWNER_CONFIRMATION_BOUNDARY",
        expected_head="4" * 40,
        allowed_scope=scope,
        issued_at=datetime(2026, 9, 8, issued_hour, tzinfo=timezone.utc),
        expires_at=datetime(2026, 9, 10, issued_hour, tzinfo=timezone.utc),
    )
    return SimpleNamespace(contract_id=identifier, contract=authority)


def test_equivalent_successor_selects_unique_newest_authority() -> None:
    older = _item("a" * 64, 8)
    newer = _item("b" * 64, 9)
    selected = RecoveringProductOwnerGateDependencyRunner._equivalent_successor((older, newer))
    assert selected is newer


def test_semantically_different_authorities_remain_ambiguous() -> None:
    older = _item("a" * 64, 8)
    newer = _item("b" * 64, 9, scope=("different",))
    assert RecoveringProductOwnerGateDependencyRunner._equivalent_successor((older, newer)) is None


def test_equal_issue_time_remains_ambiguous() -> None:
    first = _item("a" * 64, 9)
    second = _item("b" * 64, 9)
    assert RecoveringProductOwnerGateDependencyRunner._equivalent_successor((first, second)) is None
