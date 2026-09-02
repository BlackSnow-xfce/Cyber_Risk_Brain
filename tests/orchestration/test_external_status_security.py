from datetime import datetime, timezone
from pathlib import Path
from aidp_orchestration.contracts import *
from aidp_orchestration.external_status import *
from aidp_orchestration.runtime import LocalRuntimeStore

NOW=datetime(2026,1,1,tzinfo=timezone.utc)
class Repo:
 def observe(self): return RepositoryStatusObservation("a"*40,"TASK-0131","WAITING_FOR_PRODUCT_OWNER","acceptance","ARCHITECT_APPROVED","AWAITING_HUMAN",ExternalNextTask.NONE,NOW)
class Runtime:
 def observe(self,r): return RuntimeStatusObservation(blocker_code="UNKNOWN_BLOCKER",blocker_category="UNKNOWN",blocker_message="Status unavailable.",observed_at=NOW)
class Watch:
 def latest_heartbeat(self): return None

def test_projection_mutates_only_fixed_snapshot(tmp_path):
 store=LocalRuntimeStore(tmp_path); ExternalStatusProjector(Repo(),Runtime(),Watch(),store,clock=lambda:NOW).project()
 assert [p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file()]==["external-status/current.json"]

def test_canaries_and_authority_identifiers_never_serialize(tmp_path):
 store=LocalRuntimeStore(tmp_path); ExternalStatusProjector(Repo(),Runtime(),Watch(),store,clock=lambda:NOW).project()
 text=(tmp_path/"external-status/current.json").read_text()
 for forbidden in ("approval_context_id","decision_id","nonce","C:\\","https://git","<script>","Codex prompt","PID"):
  assert forbidden not in text

def test_projector_has_no_executable_or_network_imports():
 text=Path("aidp_orchestration/external_status.py").read_text(encoding="utf-8")
 for forbidden in ("AIDPLifecycleOnce","AIDPControlPlane","ProductOwnerDecisionConsumer","LifecycleProjection","subprocess","requests","socket"):
  assert forbidden not in text
