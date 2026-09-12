from pathlib import Path

from aidp_orchestration.continuation import TopologyAwareLineageContinuation
from aidp_orchestration.development_loop import DevelopmentLoopState, DevelopmentLoopStore
from aidp_orchestration.foundation import canonical_digest


def _binding(task_store: DevelopmentLoopStore, state: DevelopmentLoopState, *, automation_head="a", task_head="t"):
    effects = ()
    return {
        "task_id": state.task_id,
        "task_lineage": state.task_lineage_id,
        "topology_binding_id": "tb",
        "automation_head": automation_head,
        "task_head": task_head,
        "task_worktree": state.repository,
        "task_branch": state.branch,
        "ownership_id": "owner",
        "prior_effect_history_digest": canonical_digest(effects),
    }


def test_continuation_references_prior_history_without_rewriting(tmp_path: Path):
    task_root = tmp_path / "task"
    automation_root = tmp_path / "automation"
    task = DevelopmentLoopStore(task_root)
    original = DevelopmentLoopState("task", "lineage", 3, "BLOCKED", "repo", "branch", "old-head", terminal_reason="OLD")
    task.save(original)
    task.acquire_owner(original, "owner")

    automation = DevelopmentLoopStore(automation_root)
    consumer = TopologyAwareLineageContinuation(automation, task_root)
    checkpoint, state = consumer.prepare(
        topology_binding=_binding(task, original),
        authorization_scope_digest="scope",
    )

    assert task.load() == original
    assert checkpoint.highest_used_iteration == 3
    assert checkpoint.next_iteration == 4
    assert state.iteration == 4
    assert state.phase == "WAITING"
    assert state.expected_head == "t"
    assert automation.load() == state


def test_continuation_uses_highest_effect_iteration_and_is_idempotent(tmp_path: Path):
    task_root = tmp_path / "task"
    automation_root = tmp_path / "automation"
    task = DevelopmentLoopStore(task_root)
    original = DevelopmentLoopState("task", "lineage", 2, "WAITING", "repo", "branch", "old-head")
    task.save(original)
    task.acquire_owner(original, "owner")
    task.prepare_effect("lineage:CODEX_EXECUTION:5", {"task_lineage_id": "lineage", "iteration": 5, "effect_type": "CODEX_EXECUTION"})
    effects = tuple([task.effect("lineage:CODEX_EXECUTION:5", {})])
    binding = _binding(task, original)
    binding["prior_effect_history_digest"] = canonical_digest(effects)

    automation = DevelopmentLoopStore(automation_root)
    consumer = TopologyAwareLineageContinuation(automation, task_root)
    first, state1 = consumer.prepare(topology_binding=binding, authorization_scope_digest="scope")
    second, state2 = consumer.prepare(topology_binding=binding, authorization_scope_digest="scope")

    assert first.continuation_id == second.continuation_id
    assert state1 == state2
    assert state1.iteration == 6


def test_continuation_rejects_history_or_ownership_mismatch(tmp_path: Path):
    task_root = tmp_path / "task"
    automation_root = tmp_path / "automation"
    task = DevelopmentLoopStore(task_root)
    state = DevelopmentLoopState("task", "lineage", 1, "WAITING", "repo", "branch", "old-head")
    task.save(state)
    task.acquire_owner(state, "owner")
    automation = DevelopmentLoopStore(automation_root)
    consumer = TopologyAwareLineageContinuation(automation, task_root)

    bad = _binding(task, state)
    bad["prior_effect_history_digest"] = "wrong"
    try:
        consumer.prepare(topology_binding=bad, authorization_scope_digest="scope")
    except ValueError as exc:
        assert str(exc) == "CONTINUATION_HISTORY_DIGEST_MISMATCH"
    else:
        raise AssertionError("history mismatch accepted")

    bad = _binding(task, state)
    bad["ownership_id"] = "other"
    try:
        consumer.prepare(topology_binding=bad, authorization_scope_digest="scope")
    except ValueError as exc:
        assert str(exc) == "CONTINUATION_OWNERSHIP_MISMATCH"
    else:
        raise AssertionError("ownership mismatch accepted")
