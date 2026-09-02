from datetime import datetime, timedelta, timezone
from aidp_orchestration.contracts import *
from aidp_orchestration.external_status import *

NOW=datetime(2026,1,1,tzinfo=timezone.utc)
def repo(head="a"*40): return RepositoryStatusObservation(head,"TASK-0131","WAITING_FOR_PRODUCT_OWNER","acceptance","ARCHITECT_APPROVED","AWAITING_HUMAN",ExternalNextTask.NONE,NOW)
class Repo:
 def __init__(self, values): self.values=iter(values)
 def observe(self): return next(self.values)
class Runtime:
 def observe(self,r): return RuntimeStatusObservation("PASS","SUCCEEDED","PASSED","PRODUCT_OWNER_ACTION_REQUIRED","HUMAN","An authenticated Product Owner decision is required.",True,"PRODUCT_OWNER_DECISION",NOW)
class Watch:
 def latest_heartbeat(self): return None
class Writer:
 def persist_external_status(self,p): self.value=p

def test_stable_projection_is_allowlisted_and_published():
 w=Writer(); p=ExternalStatusProjector(Repo((repo(),repo())),Runtime(),Watch(),w,clock=lambda:NOW).project()
 assert p.consistency is ExternalConsistency.CONSISTENT and w.value==p and p.next_task is ExternalNextTask.NONE

def test_head_change_is_conflict_not_mixed():
 p=ExternalStatusProjector(Repo((repo(),repo("b"*40))),Runtime(),Watch(),Writer(),clock=lambda:NOW).project()
 assert p.consistency is ExternalConsistency.CONFLICT and p.product_head is None and p.task_id is None

def test_any_authoritative_second_read_change_is_conflict():
 second=repo(); second=RepositoryStatusObservation(second.head,second.task_id,second.lifecycle_state,"rework",second.task_status,second.product_owner_gate,second.next_task,second.observed_at,("MULTIPLE_ACTIVE_TASKS",))
 p=ExternalStatusProjector(Repo((repo(),second)),Runtime(),Watch(),Writer(),clock=lambda:NOW).project()
 assert p.consistency is ExternalConsistency.CONFLICT and p.task_id is None

def test_source_failure_is_explicit_unavailable():
 class Bad:
  def observe(self): raise OSError
 p=ExternalStatusProjector(Bad(),Runtime(),Watch(),Writer(),clock=lambda:NOW).project()
 assert p.consistency is ExternalConsistency.UNAVAILABLE
