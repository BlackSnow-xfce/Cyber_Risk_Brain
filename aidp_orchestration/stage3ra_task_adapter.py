"""Bound, non-executing adapter for the authorized Stage 3R-A lineage."""
from pathlib import Path
from dataclasses import asdict
import subprocess
from datetime import datetime, timezone
from uuid import uuid4
from .development_loop import DevelopmentLoopState, DevelopmentLoopStore
from .runtime import LocalRuntimeStore
from .contracts import CodexExecutionRequest
from .foundation import DurableCAS, canonical_digest

TASK_ID="AIDP-STAGE3R-A-REWORK"; TASK_CLASS="DEVELOPMENT_AUTOMATION"; LINEAGE="stage3ra-autonomous-rework-v1"; BRANCH="aidp/stage3ra-autonomous-rework"

class Stage3RATaskAdapter:
    def __init__(self, worktree: Path, *, expected_head: str|None, codex, reviewer, writer, runtime_store=None, status_publisher=None, ownership_id="stage3ra-autonomous-rework-v1"):
        runtime_store = runtime_store or LocalRuntimeStore.for_repository(worktree)
        self.worktree=worktree; self.expected_head=expected_head; self.codex=codex; self.reviewer=reviewer; self.writer=writer; self.runtime_store=runtime_store; self.status_publisher=status_publisher; self.ownership_id=ownership_id
        self.loop_store = DevelopmentLoopStore(runtime_store.root)

    def codex_callback(self, request, *, supervision_event=None):
        """Invoke the bound CodexExecutionService through its public API."""
        execute = getattr(self.codex, "execute", None)
        if not callable(execute):
            raise ValueError("CODEX_EXECUTION_UNAVAILABLE")
        return execute(request, supervision_event=supervision_event)

    def review_callback(self, request, *, schema_path):
        """Invoke the bound Architect review service through its public API."""
        review = getattr(self.reviewer, "review", None)
        if not callable(review):
            raise ValueError("ARCHITECT_REVIEW_UNAVAILABLE")
        return review(request, schema_path=schema_path)

    def rework_callback(self, contract):
        """Materialize rework through the bound ArchitectWriter."""
        materialize = getattr(self.writer, "materialize_rework", None)
        if not callable(materialize):
            raise ValueError("REWORK_MATERIALIZATION_UNAVAILABLE")
        return materialize(contract)

    def callbacks(self) -> tuple:
        """Return the callbacks consumed by DevelopmentLoopCoordinator."""
        callbacks = (self.codex_callback, self.review_callback, self.rework_callback)
        if not all(callable(callback) for callback in callbacks):
            raise ValueError("STAGE3RA_CALLBACKS_UNAVAILABLE")
        return callbacks

    def codex_request(self, state: DevelopmentLoopState, *, task_path: Path) -> CodexExecutionRequest:
        """Build a validated request without synthesizing authorization fields."""
        if (state.task_id != TASK_ID or state.task_lineage_id != LINEAGE or
                state.branch != BRANCH or state.repository != str(self.worktree) or
                not self.expected_head or state.expected_head != self.expected_head):
            raise ValueError("STAGE3RA_TASK_BINDING_INVALID")
        head = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=self.worktree, text=True).strip()
        branch = subprocess.check_output(("git", "branch", "--show-current"), cwd=self.worktree, text=True).strip()
        if head != state.expected_head or branch != BRANCH or subprocess.check_output(("git", "status", "--porcelain"), cwd=self.worktree, text=True):
            raise ValueError("STAGE3RA_TASK_PREFLIGHT_BLOCKED")
        if not task_path.is_file():
            raise ValueError("STAGE3RA_TASK_METADATA_UNAVAILABLE")
        return CodexExecutionRequest(
            task_id=state.task_id, task_path=task_path, repository=state.repository,
            branch=state.branch, base_commit=state.expected_head, expected_head=state.expected_head,
            phase="STAGE3R-A", allowed_scope=("STAGE3R-A",),
            prohibited_actions=("RECOVERY", "SUPERVISOR_ADMISSION", "PRODUCTION_ACTIVATION"),
            validation_requirements=("STAGE3R-A_SECURITY_REVIEW",),
            created_at=datetime.now(timezone.utc), execution_id=str(uuid4()),
            authority_instructions=("Implement only the authorized Stage 3R-A findings.",),
            rework_count=max(0, state.iteration - 1),
        )

    def reauthorize_blocked_lineage_after_uncertain_effect(self, *, authorized_head: str, reason: str):
        state = self.loop_store.load()
        if state is None or state.task_id != TASK_ID or state.task_lineage_id != LINEAGE or state.phase != "BLOCKED" or state.terminal_reason != "UNCERTAIN_CODEX_EXECUTION":
            raise ValueError("REAUTHORIZATION_PRECONDITION_DENIED")
        if not authorized_head or not reason:
            raise ValueError("REAUTHORIZATION_INPUT_INVALID")
        actual = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=self.worktree, text=True).strip()
        branch = subprocess.check_output(("git", "branch", "--show-current"), cwd=self.worktree, text=True).strip()
        if actual != authorized_head or branch != BRANCH or subprocess.check_output(("git", "status", "--porcelain"), cwd=self.worktree, text=True):
            raise ValueError("REAUTHORIZATION_WORKTREE_DENIED")
        old_key = f"{LINEAGE}:CODEX_EXECUTION:{state.iteration}"
        effect = self.loop_store.effect(old_key, {})
        if effect is None or effect.get("state") != "UNCERTAIN":
            raise ValueError("REAUTHORIZATION_EFFECT_DENIED")
        record_path = self.loop_store.cas.path.parent / "reconciliations" / (canonical_digest(f"{LINEAGE}:{state.iteration}:{authorized_head}") + ".cas")
        record_cas = DurableCAS(record_path)
        existing = record_cas.read()
        if existing is not None:
            if existing["payload"].get("authorized_head") != authorized_head:
                raise ValueError("REAUTHORIZATION_CONFLICT")
            return self.loop_store.load()
        reconciliation = {"task_id": TASK_ID, "task_lineage": LINEAGE, "prior_blocked_state_digest": canonical_digest(asdict(state)), "prior_uncertain_effect_id": old_key, "prior_uncertain_effect_digest": canonical_digest(effect), "old_expected_head": state.expected_head, "authorized_head": authorized_head, "reconciliation_id": canonical_digest(f"{LINEAGE}:{state.iteration}:{authorized_head}"), "authorization_reason": reason, "next_iteration": state.iteration + 1, "timestamp": datetime.now(timezone.utc).isoformat()}
        record_cas.compare_and_swap(expected_version=None, expected_digest=None, payload=reconciliation)
        effect_dir = self.loop_store.cas.path.parent / "effects"
        iterations = [int(item.get("iteration", 0)) for path in effect_dir.glob("*.cas") if (item := DurableCAS(path).read()) and item.get("payload", {}).get("task_lineage_id") == LINEAGE]
        next_iteration = max([state.iteration, *iterations]) + 1
        advanced = DevelopmentLoopState(TASK_ID, LINEAGE, next_iteration, "WAITING", state.repository, BRANCH, authorized_head, next_action="IMPLEMENT")
        self.loop_store.save(advanced)
        return advanced

    def reauthorize_waiting_lineage_with_stale_prepared_effect(self, *, authorized_head: str, reason: str, task_path: Path):
        state = self.loop_store.load()
        if state is None or state.phase != "WAITING" or state.task_lineage_id != LINEAGE:
            raise ValueError("REAUTHORIZATION_PRECONDITION_DENIED")
        actual = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=self.worktree, text=True).strip()
        if actual != authorized_head or subprocess.check_output(("git", "status", "--porcelain"), cwd=self.worktree, text=True):
            raise ValueError("REAUTHORIZATION_WORKTREE_DENIED")
        old_key = f"{LINEAGE}:CODEX_EXECUTION:{state.iteration + 1}"
        old = self.loop_store.effect(old_key, {})
        if old is None or old.get("state") != "PREPARED" or old.get("expected_head") == authorized_head:
            raise ValueError("REAUTHORIZATION_PREPARED_EFFECT_DENIED")
        self.loop_store.update_effect(old_key, "SUPERSEDED_BEFORE_INVOCATION")
        reconciliation = {"task_id": TASK_ID, "task_lineage": LINEAGE, "old_expected_head": state.expected_head, "authorized_head": authorized_head, "superseded_effect_id": old_key, "prior_state_digest": canonical_digest(asdict(state)), "reconciliation_id": canonical_digest(f"{LINEAGE}:{state.iteration}:{authorized_head}"), "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        rec = self.loop_store.cas.path.parent / "reconciliations" / (reconciliation["reconciliation_id"] + ".cas")
        DurableCAS(rec).compare_and_swap(expected_version=None, expected_digest=None, payload=reconciliation)
        advanced = DevelopmentLoopState(TASK_ID, LINEAGE, state.iteration + 2, "WAITING", state.repository, BRANCH, authorized_head, next_action="IMPLEMENT")
        self.loop_store.save(advanced)
        req = self.codex_request(advanced, task_path=task_path)
        key = f"{LINEAGE}:CODEX_EXECUTION:{advanced.iteration}"
        effect = self.loop_store.prepare_effect(key, {"task_lineage_id": LINEAGE, "iteration": advanced.iteration, "effect_type": "CODEX_EXECUTION", "repository": advanced.repository, "branch": BRANCH, "expected_head": authorized_head, "execution_id": req.execution_id})
        return advanced, req, effect

    def reauthorize_after_completed_blocked_codex_effect(self, *, authorized_head: str, reason: str, task_path: Path):
        state = self.loop_store.load()
        if state is None or state.phase != "WAITING" or state.task_lineage_id != LINEAGE:
            raise ValueError("REAUTHORIZATION_PRECONDITION_DENIED")
        actual = subprocess.check_output(("git", "rev-parse", "HEAD"), cwd=self.worktree, text=True).strip()
        if actual != authorized_head or subprocess.check_output(("git", "status", "--porcelain"), cwd=self.worktree, text=True):
            raise ValueError("REAUTHORIZATION_WORKTREE_DENIED")
        old_key = f"{LINEAGE}:CODEX_EXECUTION:{state.iteration + 1}"
        old = self.loop_store.effect(old_key, {})
        if old is None or old.get("state") != "COMPLETED" or old.get("result", {}).get("status") != "BLOCKED":
            raise ValueError("REAUTHORIZATION_COMPLETED_EFFECT_DENIED")
        reconciliation = {"task_id": TASK_ID, "task_lineage": LINEAGE, "prior_completed_effect_id": old_key, "prior_effect_digest": canonical_digest(old), "prior_blocked_reason": old.get("result", {}).get("failure_reason"), "old_expected_head": state.expected_head, "authorized_head": authorized_head, "next_iteration": state.iteration + 1, "reason": reason, "timestamp": datetime.now(timezone.utc).isoformat()}
        rid = canonical_digest(f"{LINEAGE}:{old_key}:{authorized_head}"); reconciliation["reconciliation_id"] = rid
        DurableCAS(self.loop_store.cas.path.parent / "reconciliations" / (rid + ".cas")).compare_and_swap(expected_version=None, expected_digest=None, payload=reconciliation)
        effect_dir = self.loop_store.cas.path.parent / "effects"
        iterations = [int(item.get("iteration", 0)) for path in effect_dir.glob("*.cas") if (item := DurableCAS(path).read()) and item.get("payload", {}).get("task_lineage_id") == LINEAGE]
        next_iteration = max([state.iteration, *iterations]) + 1
        advanced = DevelopmentLoopState(TASK_ID, LINEAGE, next_iteration, "WAITING", state.repository, BRANCH, authorized_head, next_action="IMPLEMENT")
        self.loop_store.save(advanced)
        req = self.codex_request(advanced, task_path=task_path)
        key = f"{LINEAGE}:CODEX_EXECUTION:{advanced.iteration}"
        effect = self.loop_store.prepare_effect(key, {"task_lineage_id": LINEAGE, "iteration": advanced.iteration, "effect_type": "CODEX_EXECUTION", "repository": advanced.repository, "branch": BRANCH, "expected_head": authorized_head, "execution_id": req.execution_id})
        return advanced, req, effect
    def preflight(self) -> DevelopmentLoopState:
        head=subprocess.check_output(("git","rev-parse","HEAD"),cwd=self.worktree,text=True).strip(); branch=subprocess.check_output(("git","branch","--show-current"),cwd=self.worktree,text=True).strip(); dirty=subprocess.check_output(("git","status","--porcelain"),cwd=self.worktree,text=True)
        if not self.expected_head or head!=self.expected_head or branch!=BRANCH or dirty: raise ValueError("STAGE3RA_TASK_PREFLIGHT_BLOCKED")
        state=DevelopmentLoopState(TASK_ID,LINEAGE,1,"WAITING",str(self.worktree),branch,head,next_action="IMPLEMENT")
        self.loop_store.acquire_owner(state,self.ownership_id)
        existing = self.loop_store.load()
        if existing is None:
            self.loop_store.save(state)
        elif existing != state:
            raise ValueError("STAGE3RA_TASK_STATE_CONFLICT")
        self.callbacks()
        return state
