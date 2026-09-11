from aidp_orchestration.attestations import CATEGORIES
from stage3_harness import Stage3TestTrustHarness

def test_stage3_harness_builds_independent_positive_bundle(tmp_path):
    harness=Stage3TestTrustHarness.create(tmp_path)
    manifest, members=harness.verify()
    assert len(members)==7 and set(item.category for item in members)==CATEGORIES
    assert len(set(harness.public_keys.values()))==7
    assert manifest.proposal_digest=="proposal-test"

def test_stage3_harness_isolated_from_production(tmp_path):
    harness=Stage3TestTrustHarness.create(tmp_path)
    assert harness.root==tmp_path
    assert not (tmp_path/"production").exists()
