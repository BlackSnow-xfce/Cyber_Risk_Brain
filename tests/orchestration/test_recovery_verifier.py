from datetime import datetime, timezone
from pathlib import Path

import pytest

from aidp_orchestration.recovery_verifier import ProductionGateDependencyRecoveryVerifier
from aidp_orchestration.terminal_gate_dependency_recovery import VerifiedGateDependencyRecoveryEvidence


def test_missing_provider_is_blocked_and_visible():
    verifier = ProductionGateDependencyRecoveryVerifier()
    assert verifier.readiness().state == "BLOCKED"
    assert verifier.readiness().reason == "TRUSTED_VERIFIER_UNAVAILABLE"
    with pytest.raises(PermissionError, match="TRUSTED_VERIFIER_UNAVAILABLE"):
        verifier.verify(None, predecessor=None, source=None)


def test_provider_response_must_be_authenticated_typed_evidence():
    class Provider:
        def __init__(self, value): self.value = value
        def assess(self, authority, *, predecessor, source): return self.value

    verifier = ProductionGateDependencyRecoveryVerifier(Provider(object()))
    assert verifier.readiness().state == "READY"
    with pytest.raises(PermissionError, match="untrusted"):
        verifier.verify(None, predecessor=None, source=None)


def test_typed_provider_evidence_is_returned_unchanged():
    evidence = VerifiedGateDependencyRecoveryEvidence(
        proposal_digest="a" * 64, product_owner_decision_digest="b" * 64,
        evidence_digest="c" * 64, advancement_evidence_digest="d" * 64,
        predecessor_execution_id="execution", verifier_identity="verifier",
        product_owner_identity="product-owner", permission="RECOVER_GATE_DEPENDENCY",
        approved=True, approved_advancement=True, mode="PRE_LAUNCH_FAILURE",
        pre_launch_failure_proven=True, no_active_process=True, residuals_clean=True,
        inventory_digest="e" * 64, result_digest=None, attempt_digest=None,
        execution_store_roots=(Path("C:/runtime"),),
        verified_at=datetime.now(timezone.utc),
        valid_until=datetime.now(timezone.utc),
    )
    class Provider:
        def assess(self, authority, *, predecessor, source): return evidence
    assert ProductionGateDependencyRecoveryVerifier(Provider()).verify(None, predecessor=None, source=None) is evidence
