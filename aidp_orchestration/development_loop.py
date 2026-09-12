"""Fail-closed autonomous implementation/review loop for one task lineage."""
from __future__ import annotations
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Callable, Any
from .foundation import DurableCAS, canonical_digest

PHASES = frozenset({"WAITING","IMPLEMENTING","REVIEWING","REWORKING","DONE","WAITING_FOR_HUMAN","BLOCKED"})

@dataclass(frozen=True, slots=True)
class DevelopmentLoopState:
    task_id: str; task_lineage_id: str; iteration: int; phase: str; repository: str; branch: str; expected_head: str
    codex_execution_id: str|None = None; codex_result_digest: str|None = None; architect_review_id: str|None = None
    architect_review_digest: str|None = None; last_result: str|None = None; next_action: str|None = None; terminal_reason: str|None = None

class DevelopmentLoopStore:
    def __init__(self, root: Path): self.cas = DurableCAS(root / "development-loop.cas")
    def load(self) -> DevelopmentLoopState|None:
        record=self.cas.read(); return None if record is None else DevelopmentLoopState(**record["payload"])
    def save(self, state: DevelopmentLoopState) -> DevelopmentLoopState:
        if state.phase not in PHASES: raise ValueError("invalid development loop phase")
        current=self.cas.read(); self.cas.compare_and_swap(expected_version=None if current is None else current["version"], expected_digest=None if current is None else current["digest"], payload=asdict(state)); return state
    def effect(self, key: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        path=self.cas.path.parent / "effects" / (canonical_digest(key) + ".cas"); cas=DurableCAS(path); return None if cas.read() is None else cas.read()["payload"]
    def prepare_effect(self, key: str, payload: dict[str, Any]) -> dict[str, Any]:
        path=self.cas.path.parent / "effects" / (canonical_digest(key) + ".cas"); cas=DurableCAS(path); current=cas.read()
        if current is not None: return current["payload"]
        value={**payload,"idempotency_key":key,"state":"PREPARED"}; cas.compare_and_swap(expected_version=None,expected_digest=None,payload=value); return value
    def update_effect(self, key: str, state: str, **values: Any) -> dict[str, Any]:
        path=self.cas.path.parent / "effects" / (canonical_digest(key) + ".cas"); cas=DurableCAS(path); current=cas.read()
        if current is None: raise ValueError("effect unavailable")
        payload={**current["payload"],"state":state,**values}; cas.compare_and_swap(expected_version=current["version"],expected_digest=current["digest"],payload=payload); return payload
    def acquire_owner(self, state: DevelopmentLoopState, ownership_id: str) -> None:
        path=self.cas.path.parent / "lineage-owner.cas"; cas=DurableCAS(path); current=cas.read(); owner={"task_lineage_id":state.task_lineage_id,"task_id":state.task_id,"repository":state.repository,"branch":state.branch,"expected_head":state.expected_head,"ownership_id":ownership_id}
        if current is not None and current["payload"] != owner: raise ValueError("active lineage ownership conflict")
        if current is None: cas.compare_and_swap(expected_version=None, expected_digest=None, payload=owner)
    def verify_owner(self, state: DevelopmentLoopState, ownership_id: str) -> None:
        current=self.cas.path.parent / "lineage-owner.cas"; record=DurableCAS(current).read()
        if record is None or record["payload"].get("ownership_id") != ownership_id or any(record["payload"].get(k)!=getattr(state,k) for k in ("task_lineage_id","task_id","repository","branch","expected_head")): raise ValueError("lineage ownership mismatch")

class DevelopmentLoopCoordinator:
    def __init__(self, store: DevelopmentLoopStore, *, codex: Callable[[DevelopmentLoopState], Any], review: Callable[[DevelopmentLoopState, Any], Any], rework: Callable[[DevelopmentLoopState, Any], Any]|None=None, head: Callable[[], str]|None=None, ownership_id: str="default", status: Callable[[DevelopmentLoopState], None]|None=None):
        self.store,self.codex,self.review,self.rework,self.head,self.ownership_id,self.status=store,codex,review,rework,head,ownership_id,status
    def _publish(self, state, automation):
        if self.status: self.status(replace(state, phase=automation))
    def run_once(self) -> DevelopmentLoopState:
        state=self.store.load()
        if state is None: raise ValueError("development loop state unavailable")
        self.store.acquire_owner(state, self.ownership_id); self.store.verify_owner(state, self.ownership_id)
        if state.phase in {"DONE","BLOCKED","WAITING_FOR_HUMAN"}: return state
        if self.head is not None and self.head()!=state.expected_head: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"STALE_REPOSITORY_HEAD","next_action":"STOP"}))
        if state.phase=="WAITING": state=self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"IMPLEMENTING","next_action":"INVOKE_CODEX"}))
        if state.phase=="IMPLEMENTING":
            key=f"{state.task_lineage_id}:CODEX_EXECUTION:{state.iteration}"; effect=self.store.prepare_effect(key,{"task_lineage_id":state.task_lineage_id,"iteration":state.iteration,"effect_type":"CODEX_EXECUTION","repository":state.repository,"branch":state.branch,"expected_head":state.expected_head})
            if effect.get("state") in {"IN_FLIGHT","UNCERTAIN"}: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"UNCERTAIN_CODEX_EXECUTION","next_action":"STOP"}))
            if effect.get("state")=="COMPLETED": result=effect.get("result", {"execution_id":effect.get("external_id")})
            else:
                self.store.update_effect(key,"IN_FLIGHT");
                try: result=self.codex(state)
                except Exception:
                    self.store.update_effect(key,"UNCERTAIN"); return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"UNCERTAIN_CODEX_EXECUTION","next_action":"STOP"}))
                if not isinstance(result,dict) or not result.get("execution_id"): return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"MALFORMED_CODEX_RESULT","next_action":"STOP"}))
                digest=canonical_digest(result); self.store.update_effect(key,"COMPLETED",external_id=result["execution_id"],result_digest=digest,result=result)
            
            self._publish(state, "WORKING"); digest=canonical_digest(result); state=self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"REVIEWING","codex_execution_id":result["execution_id"],"codex_result_digest":digest,"last_result":"CODEX_COMPLETE","next_action":"INVOKE_REVIEW"}))
        if state.phase=="REVIEWING":
            key=f"{state.task_lineage_id}:ARCHITECT_REVIEW:{state.iteration}"; effect=self.store.prepare_effect(key,{"task_lineage_id":state.task_lineage_id,"iteration":state.iteration,"effect_type":"ARCHITECT_REVIEW","repository":state.repository,"branch":state.branch,"expected_head":state.expected_head})
            if effect.get("state") in {"IN_FLIGHT","UNCERTAIN"}: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"UNCERTAIN_ARCHITECT_REVIEW","next_action":"STOP"}))
            if effect.get("state")=="COMPLETED": result=effect.get("result", {"review_id":effect.get("external_id"),"decision":"APPROVED"})
            else:
                self.store.update_effect(key,"IN_FLIGHT"); self._publish(state, "REVIEWING")
                try: result=self.review(state, state.codex_result_digest)
                except Exception:
                    self.store.update_effect(key,"UNCERTAIN"); return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"UNCERTAIN_ARCHITECT_REVIEW","next_action":"STOP"}))
            if not isinstance(result,dict) or not result.get("review_id") or result.get("decision") not in {"APPROVED","CHANGES_REQUIRED","NOT_APPROVED","HUMAN_GATE"}: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"MALFORMED_REVIEW","next_action":"STOP"}))
            review_digest=canonical_digest(result)
            if effect.get("state")!="COMPLETED": self.store.update_effect(key,"COMPLETED",external_id=result["review_id"],result_digest=review_digest,result=result)
            if result["decision"]=="APPROVED":
                done=self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"DONE","architect_review_id":result["review_id"],"architect_review_digest":review_digest,"last_result":"APPROVED","next_action":"DONE"})); self._publish(done,"DONE"); return done
            if result.get("decision")=="HUMAN_GATE" or result.get("gate_type") in {"PRODUCT_OWNER_APPROVAL","RECOVERY_AUTHORIZATION","PRODUCTION_ACTIVATION","SCOPE_EXPANSION"}: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"WAITING_FOR_HUMAN","terminal_reason":result.get("gate_type","HUMAN_GATE"),"next_action":"WAIT_FOR_HUMAN"}))
            if self.rework is None: return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"REWORK_UNAVAILABLE","next_action":"STOP"}))
            key=f"{state.task_lineage_id}:REWORK_MATERIALIZATION:{state.iteration}:{canonical_digest(result)}"; effect=self.store.prepare_effect(key,{"task_lineage_id":state.task_lineage_id,"iteration":state.iteration,"effect_type":"REWORK_MATERIALIZATION","repository":state.repository,"branch":state.branch,"expected_head":state.expected_head})
            if effect.get("state") in {"PREPARED","IN_FLIGHT"}:
                self.store.update_effect(key,"IN_FLIGHT");
                self._publish(state, "REWORKING")
                try: materialized=self.rework(state,result)
                except Exception:
                    self.store.update_effect(key,"UNCERTAIN"); return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"BLOCKED","terminal_reason":"UNCERTAIN_REWORK_MATERIALIZATION","next_action":"STOP"}))
                self.store.update_effect(key,"COMPLETED",external_id=str(materialized or "rework"),result_digest=canonical_digest(result))
            return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"REWORKING","iteration":state.iteration+1,"last_result":"REWORK_MATERIALIZED","next_action":"AUTHORIZE_NEXT_ITERATION"}))
        if state.phase=="REWORKING": return self.store.save(DevelopmentLoopState(**{**asdict(state),"phase":"IMPLEMENTING","next_action":"INVOKE_CODEX"}))
        return state
