from aidp_orchestration.development_loop import DevelopmentLoopState, DevelopmentLoopStore, DevelopmentLoopCoordinator

def test_loop_approved(tmp_path):
    store=DevelopmentLoopStore(tmp_path); store.save(DevelopmentLoopState("t","l",1,"WAITING","r","b","h"))
    c=DevelopmentLoopCoordinator(store,codex=lambda s:{"execution_id":"e"},review=lambda s,r:{"review_id":"v","decision":"APPROVED"})
    assert c.run_once().phase=="DONE"

def test_loop_rework_then_approve(tmp_path):
    store=DevelopmentLoopStore(tmp_path); store.save(DevelopmentLoopState("t","l",1,"WAITING","r","b","h")); n=[0]
    def review(s,r): n[0]+=1; return {"review_id":str(n[0]),"decision":"CHANGES_REQUIRED" if n[0]==1 else "APPROVED"}
    c=DevelopmentLoopCoordinator(store,codex=lambda s:{"execution_id":str(s.iteration)},review=review,rework=lambda s,r:None)
    c.run_once(); assert c.run_once().phase=="IMPLEMENTING"; c.run_once(); assert c.run_once().phase=="DONE"

def test_stale_head_blocks(tmp_path):
    store=DevelopmentLoopStore(tmp_path); store.save(DevelopmentLoopState("t","l",1,"WAITING","r","b","h"))
    c=DevelopmentLoopCoordinator(store,codex=lambda s:{"execution_id":"e"},review=lambda s,r:{},head=lambda:"changed")
    assert c.run_once().phase=="BLOCKED"
