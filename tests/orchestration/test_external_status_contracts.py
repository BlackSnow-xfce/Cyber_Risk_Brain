from datetime import datetime, timezone
import pytest
from aidp_orchestration.contracts import *

NOW=datetime(2026,1,1,tzinfo=timezone.utc)

def values():
    return dict(schema_version="aidp-external-status-v1",generated_at=NOW,repository_id="predatorai-product",product_head="a"*40,head_status="CURRENT",task_id="TASK-0131",task_phase="acceptance",task_status="ARCHITECT_APPROVED",lifecycle_state="WAITING_FOR_PRODUCT_OWNER",product_owner_gate="AWAITING_HUMAN",architect_status="PASS",execution_status="SUCCEEDED",validation_summary="PASSED",watcher_status=ExternalWatcherHealth.ACTIVE,watcher_last_activity_at=NOW,watcher_activity_age_seconds=0,watcher_last_outcome=ExternalWatcherOutcome.NO_ACTION,blocker_code="PRODUCT_OWNER_ACTION_REQUIRED",blocker_category="HUMAN",blocker_message="An authenticated Product Owner decision is required.",human_action_required=True,human_action_kind="PRODUCT_OWNER_DECISION",next_task=ExternalNextTask.NONE,consistency=ExternalConsistency.CONSISTENT,consistency_issues=(),oldest_observation_at=NOW)

def test_projection_is_closed_and_digest_bound():
    v=values(); p=ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v)
    assert p.repository_id=="predatorai-product"

def test_alias_commit_and_digest_are_strict():
    for field,bad in (("repository_id","path/C:"),("product_head","abc")):
        v=values(); v[field]=bad
        with pytest.raises(ValueError): ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v)

def test_exists_is_reserved_but_valid():
    v=values(); v["next_task"]=ExternalNextTask.EXISTS
    assert ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v).next_task is ExternalNextTask.EXISTS

def test_unbounded_or_unknown_disclosure_values_are_rejected():
    for field,bad in (("task_status","RAW INTERNAL"),("task_phase","x"*65),("blocker_message","x"*161)):
        v=values(); v[field]=bad
        with pytest.raises(ValueError): ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v)
    for field,bad in (("blocker_code","ATTACKER_CODE"),("consistency_issues",("ATTACKER\nPATH",)),("human_action_kind","NONE")):
        v=values(); v[field]=bad
        with pytest.raises(ValueError): ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v)
    for control in ("\t","\x7f","\u202e"):
        v=values(); v["blocker_message"]="unsafe"+control
        with pytest.raises(ValueError): ExternalStatusProjectionV1(projection_id=canonical_digest(v),**v)
