from pathlib import Path

from aidp_orchestration.runtime import LocalRuntimeStore
from aidp_orchestration.stage3ra_task_adapter import Stage3RATaskAdapter


class _Codex:
    def execute(self, request, supervision_event=None):
        return ("codex", request, supervision_event)


class _Reviewer:
    def review(self, request, *, schema_path):
        return ("review", request, schema_path)


class _Writer:
    def materialize_rework(self, contract):
        return ("rework", contract)


def test_live_service_callbacks_are_exposed(tmp_path: Path):
    adapter = Stage3RATaskAdapter(
        tmp_path,
        expected_head="unused",
        codex=_Codex(), reviewer=_Reviewer(), writer=_Writer(),
        runtime_store=LocalRuntimeStore(tmp_path / "runtime"),
        status_publisher=None,
    )
    callbacks = adapter.callbacks()
    assert len(callbacks) == 3
    assert adapter.codex_callback("request")[0] == "codex"
    assert adapter.review_callback("request", schema_path=tmp_path / "schema")[0] == "review"
    assert adapter.rework_callback("contract")[0] == "rework"


def test_preflight_initializes_shared_loop_state(tmp_path: Path):
    worktree = Path(r"D:\CyberRiskBrain-stage3ra-autonomous-rework")
    import subprocess
    from unittest.mock import patch
    head = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=worktree, text=True).strip()
    adapter = Stage3RATaskAdapter(
        worktree,
        expected_head=head,
        codex=_Codex(), reviewer=_Reviewer(), writer=_Writer(),
        runtime_store=LocalRuntimeStore(tmp_path / "runtime"),
        status_publisher=None,
    )
    with patch("aidp_orchestration.stage3ra_task_adapter.subprocess.check_output", side_effect=(head, "aidp/stage3ra-autonomous-rework", "")):
        state = adapter.preflight()
    assert adapter.loop_store.load() == state
    assert state.next_action == "IMPLEMENT"
    with patch("aidp_orchestration.stage3ra_task_adapter.subprocess.check_output", side_effect=(head, "aidp/stage3ra-autonomous-rework", "")):
        assert adapter.preflight() == state


def test_codex_request_adapter_validates_bound_state(tmp_path: Path):
    from aidp_orchestration.development_loop import DevelopmentLoopState
    from unittest.mock import patch
    worktree = Path(r"D:\CyberRiskBrain-stage3ra-autonomous-rework")
    head = "h" * 40
    adapter = Stage3RATaskAdapter(worktree, expected_head=head, codex=_Codex(), reviewer=_Reviewer(), writer=_Writer(), runtime_store=LocalRuntimeStore(tmp_path / "runtime"))
    state = DevelopmentLoopState("AIDP-STAGE3R-A-REWORK", "stage3ra-autonomous-rework-v1", 1, "WAITING", str(worktree), "aidp/stage3ra-autonomous-rework", head)
    task = tmp_path / "task.md"; task.write_text("authorized")
    with patch("aidp_orchestration.stage3ra_task_adapter.subprocess.check_output", side_effect=(head, "aidp/stage3ra-autonomous-rework", "")):
        request = adapter.codex_request(state, task_path=task)
    assert request.task_id == state.task_id
