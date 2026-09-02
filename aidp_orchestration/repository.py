"""Read-only deterministic inspection of repository AIDP artifacts."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path
from uuid import uuid4

from .contracts import (
    AIDPState,
    AuditEvent,
    CodexExecutionRequest,
    CodexExecutionResult,
    ExecutionStatus,
    Handoff,
    OrchestrationDecision,
    ScopeCompliance,
    TaskMetadata,
    ValidationResult,
    ensure_non_empty,
    utc_now,
)


_FRONT_MATTER = re.compile(r"\A---\s*\n(?P<body>.*?)\n---\s*\n", re.DOTALL)
_KEY = re.compile(r"^(?P<key>[a-z_]+):\s*(?P<value>.*)$")


class AIDPRepository:
    """Inspects state and creates requests without mutating the repository."""

    def __init__(self, root: Path):
        self.root = root.resolve()
        self.ai_root = self.root / ".ai"

    @property
    def branch(self) -> str:
        return self._git("branch", "--show-current").strip()

    @property
    def head(self) -> str:
        return self._git("rev-parse", "HEAD").strip()

    def task_paths(self, state_dir: str) -> tuple[Path, ...]:
        directory = self.ai_root / "tasks" / state_dir
        if not directory.exists():
            return ()
        candidates = (*directory.glob("TASK-*.md"), *directory.glob("AIDP-INFRA-*.md"))
        return tuple(sorted(
            path for path in candidates
            if re.fullmatch(r"(?:TASK-(?:\d{4}|E2E-(?:(?:WRITER|TRIGGER)-)?\d{4})|AIDP-INFRA-\d{4})", path.stem)
        ))

    def inspect(self) -> OrchestrationDecision:
        ready = self.task_paths("ready")
        review = self.task_paths("review")
        branch, commit = self.branch, self.head
        reasons: list[str] = []

        if ready and review:
            return self._blocked(None, branch, commit, "READY and REVIEW tasks coexist")
        if len(ready) > 1:
            return self._blocked(None, branch, commit, "multiple READY tasks")
        if len(review) > 1:
            return self._blocked(None, branch, commit, "multiple active REVIEW tasks")
        if ready:
            task_id = ready[0].stem
            if not self._handoffs_match(task_id, expected_review=False):
                return self._blocked(task_id, branch, commit, "handoff/task state conflict")
            metadata = self.parse_metadata(ready[0])
            if metadata is None:
                reasons.append("execution scope metadata is not explicit")
                return OrchestrationDecision(task_id, AIDPState.BLOCKED, None, branch, commit, tuple(reasons), utc_now())
            return OrchestrationDecision(task_id, AIDPState.READY_FOR_CODEX, AIDPState.CODEX_RUNNING, branch, commit, (), utc_now())
        if review:
            task_id = review[0].stem
            task_text = review[0].read_text(encoding="utf-8")
            status = self._explicit_status(task_text)
            if status == "REVIEW / REWORK REQUIRED":
                next_state = AIDPState.READY_FOR_CODEX if self.parse_metadata(review[0]) else None
                reasons.append("architect explicitly requires rework")
                if next_state is None:
                    reasons.append("rework scope metadata is not explicit")
                    state = AIDPState.BLOCKED
                else:
                    state = AIDPState.REWORK_REQUIRED
                return OrchestrationDecision(task_id, state, next_state, branch, commit, tuple(reasons), utc_now())
            if status == "ARCHITECT_APPROVED":
                metadata = self.parse_metadata(review[0])
                if metadata and metadata.product_owner_gate:
                    return OrchestrationDecision(task_id, AIDPState.WAITING_FOR_PRODUCT_OWNER, None, branch, commit, (), utc_now())
                return OrchestrationDecision(task_id, AIDPState.ARCHITECT_APPROVED, AIDPState.DONE, branch, commit, (), utc_now())
            if status == "PRODUCT OWNER REWORK REQUESTED":
                return OrchestrationDecision(
                    task_id, AIDPState.PRODUCT_OWNER_REWORK_REQUESTED, None,
                    branch, commit, ("Architect rework planning authority is required",), utc_now(),
                )
            if not self._handoffs_match(task_id, expected_review=True):
                return self._blocked(task_id, branch, commit, "handoff/task state conflict")
            return OrchestrationDecision(task_id, AIDPState.READY_FOR_ARCHITECT, None, branch, commit, (), utc_now())
        done_handoff = self.parse_handoff(self.ai_root / "handoff" / "TO-CODEX.md")
        if done_handoff.status == "CLOSED" and done_handoff.task_id:
            done = tuple(path for path in self.task_paths("done") if path.stem == done_handoff.task_id)
            if len(done) == 1 and self._explicit_status(done[0].read_text(encoding="utf-8")) == "DONE / PASS / APPROVED":
                return OrchestrationDecision(done[0].stem, AIDPState.DONE, None, branch, commit, (), utc_now())
        return OrchestrationDecision(None, AIDPState.WAITING, None, branch, commit, (), utc_now())

    def build_execution_request(self, task_id: str, *, rework_count: int = 0) -> CodexExecutionRequest:
        candidates = [path for path in (*self.task_paths("ready"), *self.task_paths("review")) if path.stem == task_id]
        if len(candidates) != 1:
            raise ValueError("exactly one active task is required")
        path = candidates[0]
        metadata = self.parse_metadata(path)
        if metadata is None or metadata.task_id != task_id:
            raise ValueError("task requires explicit execution metadata")
        decision = self.inspect()
        if decision.state not in {AIDPState.READY_FOR_CODEX, AIDPState.REWORK_REQUIRED}:
            raise ValueError(f"task is not executable in state {decision.state}")
        return CodexExecutionRequest(
            task_id=task_id,
            task_path=path,
            repository=str(self.root),
            branch=self.branch,
            base_commit=self.head,
            expected_head=self.head,
            phase=metadata.phase,
            allowed_scope=metadata.allowed_scope,
            prohibited_actions=metadata.prohibited_actions,
            validation_requirements=metadata.validation_requirements,
            created_at=utc_now(),
            execution_id=str(uuid4()),
            rework_count=rework_count,
        )

    def evaluate_result(self, request: CodexExecutionRequest, result: CodexExecutionResult) -> AIDPState:
        if self.head != request.expected_head:
            return AIDPState.STALE_EXECUTION
        if result.scope_compliance is not ScopeCompliance.COMPLIANT:
            return AIDPState.BLOCKED
        if not result.is_review_ready:
            return AIDPState.BLOCKED
        return AIDPState.READY_FOR_ARCHITECT

    def validate_scope(self, request: CodexExecutionRequest, changed_files: tuple[str, ...]) -> ScopeCompliance:
        return self.scope_compliance_for_paths(
            request.allowed_scope,
            request.prohibited_actions,
            changed_files,
        )

    @staticmethod
    def scope_compliance_for_paths(
        allowed: tuple[str, ...],
        prohibited: tuple[str, ...],
        changed_files: tuple[str, ...],
    ) -> ScopeCompliance:
        for path in changed_files:
            if any(fnmatch.fnmatch(path, pattern) for pattern in prohibited):
                return ScopeCompliance.VIOLATION
            if not any(fnmatch.fnmatch(path, pattern) for pattern in allowed):
                return ScopeCompliance.VIOLATION
        return ScopeCompliance.COMPLIANT

    def parse_metadata(self, path: Path) -> TaskMetadata | None:
        match = _FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if not match:
            return None
        values: dict[str, str] = {}
        for line in match.group("body").splitlines():
            parsed = _KEY.match(line.strip())
            if parsed:
                values[parsed.group("key")] = parsed.group("value").strip()
        required = {"task_id", "phase", "allowed_scope", "prohibited_actions", "validation_requirements"}
        if not required.issubset(values):
            return None
        def list_value(name: str) -> tuple[str, ...]:
            raw = values[name]
            return ensure_non_empty(tuple(item.strip() for item in raw.split(",")), name)
        return TaskMetadata(
            task_id=values["task_id"],
            phase=values["phase"],
            allowed_scope=list_value("allowed_scope"),
            prohibited_actions=list_value("prohibited_actions"),
            validation_requirements=list_value("validation_requirements"),
            product_owner_gate=values.get("product_owner_gate", "false").lower() == "true",
        )

    def parse_handoff(self, path: Path) -> Handoff:
        text = path.read_text(encoding="utf-8")
        status = self._first_value(text, "Status") or ""
        task_value = self._first_value(text, "Current AIDP Task") or self._first_value(text, "Task")
        task_match = re.search(r"(?:TASK-\d{4}|AIDP-INFRA-\d{4})", task_value or "")
        task_id = task_match.group(0) if task_match else task_value
        task_status = self._first_value(text, "Task Status")
        return Handoff(status, task_id, task_status)

    def _handoffs_match(self, task_id: str, *, expected_review: bool) -> bool:
        codex = self.parse_handoff(self.ai_root / "handoff" / "TO-CODEX.md")
        architect = self.parse_handoff(self.ai_root / "handoff" / "TO-ARCHITECT.md")
        if codex.task_id != task_id or architect.task_id != task_id:
            return False
        if expected_review:
            return codex.status == "WAITING" and architect.status == "OPEN"
        return codex.status == "OPEN" and architect.status in {"WAITING", "CLOSED"}

    def _blocked(self, task_id: str | None, branch: str, commit: str, reason: str) -> OrchestrationDecision:
        return OrchestrationDecision(task_id, AIDPState.BLOCKED, None, branch, commit, (reason,), utc_now())

    @staticmethod
    def _first_value(text: str, label: str) -> str | None:
        match = re.search(
            rf"(?m)^\*{{0,2}}{re.escape(label)}\*{{0,2}}:\*{{0,2}}\s*(.+?)\s*$",
            text,
        )
        return match.group(1).strip() if match else None

    @staticmethod
    def _explicit_status(text: str) -> str | None:
        for label in ("Status", "Task Status"):
            value = AIDPRepository._first_value(text, label)
            if value:
                return value
        return None

    def _git(self, *args: str) -> str:
        return subprocess.check_output(("git", *args), cwd=self.root, text=True).strip()
