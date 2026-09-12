"""Topology-aware, read-only continuation of a preserved development-loop lineage."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .development_loop import DevelopmentLoopState, DevelopmentLoopStore
from .foundation import DurableCAS, canonical_digest


@dataclass(frozen=True, slots=True)
class TopologyAwareContinuationCheckpointV1:
    task_id: str
    task_lineage: str
    topology_binding_id: str
    automation_head: str
    task_head: str
    source_task_runtime_identity: str
    prior_state_digest: str
    prior_effect_history_digest: str
    highest_used_iteration: int
    next_iteration: int
    continuation_id: str
    ownership_id: str
    authorization_scope_digest: str
    created_at: str


class TopologyAwareLineageContinuation:
    """Reference prior task history without rewriting it and create a new automation continuation."""

    def __init__(self, automation_store: DevelopmentLoopStore, task_runtime_root: Path):
        self.automation_store = automation_store
        self.task_runtime_root = Path(task_runtime_root)

    def _task_store(self) -> DevelopmentLoopStore:
        return DevelopmentLoopStore(self.task_runtime_root)

    def _effect_payloads(self, lineage: str) -> tuple[dict[str, Any], ...]:
        effects = self.task_runtime_root / "effects"
        if not effects.exists():
            return ()
        values: list[dict[str, Any]] = []
        for path in sorted(effects.glob("*.cas")):
            try:
                record = DurableCAS(path).read()
            except Exception as exc:
                raise ValueError("CONTINUATION_EFFECT_HISTORY_UNREADABLE") from exc
            if record is None:
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict):
                raise ValueError("CONTINUATION_EFFECT_HISTORY_INVALID")
            if payload.get("task_lineage_id") == lineage:
                values.append(dict(payload))
        return tuple(values)

    def _owner(self) -> dict[str, Any]:
        path = self.task_runtime_root / "lineage-owner.cas"
        record = DurableCAS(path).read()
        if record is None or not isinstance(record.get("payload"), dict):
            raise ValueError("CONTINUATION_OWNERSHIP_UNAVAILABLE")
        return dict(record["payload"])

    def prepare(
        self,
        *,
        topology_binding: dict[str, Any],
        authorization_scope_digest: str,
    ) -> tuple[TopologyAwareContinuationCheckpointV1, DevelopmentLoopState]:
        required = {
            "task_id",
            "task_lineage",
            "topology_binding_id",
            "automation_head",
            "task_head",
            "task_worktree",
            "task_branch",
            "ownership_id",
            "prior_effect_history_digest",
        }
        if not required.issubset(topology_binding) or not authorization_scope_digest:
            raise ValueError("CONTINUATION_TOPOLOGY_INVALID")

        task_store = self._task_store()
        prior_state = task_store.load()
        if prior_state is None:
            raise ValueError("CONTINUATION_STATE_UNAVAILABLE")
        if prior_state.task_id != topology_binding["task_id"] or prior_state.task_lineage_id != topology_binding["task_lineage"]:
            raise ValueError("CONTINUATION_LINEAGE_MISMATCH")

        owner = self._owner()
        if owner.get("ownership_id") != topology_binding["ownership_id"] or owner.get("task_id") != prior_state.task_id or owner.get("task_lineage_id") != prior_state.task_lineage_id:
            raise ValueError("CONTINUATION_OWNERSHIP_MISMATCH")

        effects = self._effect_payloads(prior_state.task_lineage_id)
        highest_used = max([prior_state.iteration, *(int(item.get("iteration", 0)) for item in effects)], default=prior_state.iteration)
        history_digest = canonical_digest(effects)
        if topology_binding["prior_effect_history_digest"] != history_digest:
            raise ValueError("CONTINUATION_HISTORY_DIGEST_MISMATCH")

        prior_state_digest = canonical_digest(asdict(prior_state))
        next_iteration = highest_used + 1
        identity_payload = {
            "task_id": prior_state.task_id,
            "task_lineage": prior_state.task_lineage_id,
            "topology_binding_id": topology_binding["topology_binding_id"],
            "automation_head": topology_binding["automation_head"],
            "task_head": topology_binding["task_head"],
            "prior_state_digest": prior_state_digest,
            "prior_effect_history_digest": history_digest,
            "highest_used_iteration": highest_used,
            "next_iteration": next_iteration,
            "ownership_id": topology_binding["ownership_id"],
            "authorization_scope_digest": authorization_scope_digest,
        }
        continuation_id = canonical_digest(identity_payload)
        path = self.automation_store.cas.path.parent / "continuations" / f"{continuation_id}.cas"
        cas = DurableCAS(path)
        existing = cas.read()

        if existing is not None:
            stored = existing.get("payload")
            if not isinstance(stored, dict):
                raise ValueError("CONTINUATION_CONFLICT")
            stable = {key: stored.get(key) for key in identity_payload}
            expected_stable = {
                "task_id": prior_state.task_id,
                "task_lineage": prior_state.task_lineage_id,
                "topology_binding_id": topology_binding["topology_binding_id"],
                "automation_head": topology_binding["automation_head"],
                "task_head": topology_binding["task_head"],
                "prior_state_digest": prior_state_digest,
                "prior_effect_history_digest": history_digest,
                "highest_used_iteration": highest_used,
                "next_iteration": next_iteration,
                "ownership_id": topology_binding["ownership_id"],
                "authorization_scope_digest": authorization_scope_digest,
            }
            if stable != expected_stable or stored.get("continuation_id") != continuation_id:
                raise ValueError("CONTINUATION_CONFLICT")
            checkpoint = TopologyAwareContinuationCheckpointV1(**stored)
        else:
            checkpoint = TopologyAwareContinuationCheckpointV1(
                task_id=prior_state.task_id,
                task_lineage=prior_state.task_lineage_id,
                topology_binding_id=topology_binding["topology_binding_id"],
                automation_head=topology_binding["automation_head"],
                task_head=topology_binding["task_head"],
                source_task_runtime_identity=canonical_digest(str(self.task_runtime_root.resolve())),
                prior_state_digest=prior_state_digest,
                prior_effect_history_digest=history_digest,
                highest_used_iteration=highest_used,
                next_iteration=next_iteration,
                continuation_id=continuation_id,
                ownership_id=topology_binding["ownership_id"],
                authorization_scope_digest=authorization_scope_digest,
                created_at=datetime.now(timezone.utc).isoformat(),
            )
            cas.compare_and_swap(expected_version=None, expected_digest=None, payload=asdict(checkpoint))

        state = DevelopmentLoopState(
            prior_state.task_id,
            prior_state.task_lineage_id,
            next_iteration,
            "WAITING",
            topology_binding["task_worktree"],
            topology_binding["task_branch"],
            topology_binding["task_head"],
            next_action="IMPLEMENT",
        )
        current = self.automation_store.load()
        if current is None:
            self.automation_store.save(state)
        elif current != state:
            raise ValueError("CONTINUATION_STATE_CONFLICT")
        return checkpoint, state
