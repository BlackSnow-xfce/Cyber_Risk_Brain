from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import threading

import pytest

from aidp_orchestration.architect_review import create_review_result
from aidp_orchestration.contracts import (
    AIDPState, ArchitectReviewDisposition, ArchitectReviewProvenance,
    AuthenticatedProductOwner, ProductOwnerAcceptanceStatus,
    ProductOwnerAuthorizationEvidence, ProductOwnerOperation,
)
from aidp_orchestration.lifecycle_projection import LifecycleProjection
from aidp_orchestration.product_owner_acceptance import ProductOwnerDecisionConsumer
from aidp_orchestration.product_owner_confirmation import (
    ApprovalContextIssuer, ProductOwnerConfirmationCommand,
    ProductOwnerConfirmationService,
)
from aidp_orchestration.repository import AIDPRepository
from aidp_orchestration.runtime import LocalRuntimeStore


NOW = datetime(2026, 9, 2, tzinfo=timezone.utc)
NONCE = "secure-single-use-nonce-value-0000000001"


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(("git", *args), cwd=root, text=True).strip()


def fixture(tmp_path: Path):
    root, remote = tmp_path / "product", tmp_path / "remote.git"
    root.mkdir()
    subprocess.check_call(("git", "init", "-q", "-b", "topic"), cwd=root)
    subprocess.check_call(("git", "init", "-q", "--bare", str(remote)))
    git(root, "config", "user.name", "AIDP Test")
    git(root, "config", "user.email", "aidp@example.test")
    git(root, "remote", "add", "origin", str(remote))
    review = root / ".ai/tasks/review/TASK-0131.md"
    review.parent.mkdir(parents=True)
    (root / ".ai/handoff").mkdir(parents=True)
    review.write_text(
        "---\ntask_id: TASK-0131\nphase: acceptance\nallowed_scope: a.py\n"
        "prohibited_actions: product/**\nvalidation_requirements: pytest\n"
        "product_owner_gate: true\n---\nStatus: REVIEW\n", encoding="utf-8",
    )
    (root / ".ai/handoff/TO-CODEX.md").write_text(
        "Status: WAITING\nCurrent AIDP Task: TASK-0131\nTask Status: REVIEW\n", encoding="utf-8",
    )
    (root / ".ai/handoff/TO-ARCHITECT.md").write_text(
        "Status: OPEN\nTask: TASK-0131\nTask Status: REVIEW\n", encoding="utf-8",
    )
    git(root, "add", ".ai")
    git(root, "commit", "-q", "-m", "base")
    base = git(root, "rev-parse", "HEAD")
    review.write_text(review.read_text(encoding="utf-8").replace("Status: REVIEW", "Status: ARCHITECT_APPROVED"), encoding="utf-8")
    git(root, "add", ".ai/tasks/review/TASK-0131.md")
    git(root, "commit", "-q", "-m", "architect pass")
    product_commit = git(root, "rev-parse", "HEAD")
    git(root, "push", "-q", "-u", "origin", "topic")
    result = create_review_result(
        review_request_id="1" * 64, task_id="TASK-0131", execution_id="execution-1",
        review_iteration=0, disposition=ArchitectReviewDisposition.PASS,
        reviewed_head="2" * 40, expected_head=base, reviewed_tree_hash="3" * 40,
        findings=(), allowed_rework_scope=(), required_validations=(),
        provenance=ArchitectReviewProvenance("process", "launcher", "model", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    repository = AIDPRepository(root)
    store = LocalRuntimeStore.for_repository(root)
    store.persist_architect_result(result)
    assert repository.inspect().state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    return root, repository, store, product_commit


class Authenticator:
    def authenticate(self, proof, context):
        if proof != "trusted-oidc-confirmation":
            raise PermissionError
        return AuthenticatedProductOwner(
            "po-1", "enterprise-issuer", "subject", "auth-event", NOW,
            "oidc-step-up", "high", "session-reference",
        )


class Authorizer:
    def __init__(self, allowed=True): self.allowed = allowed
    def authorize(self, principal, context, operation, *, at):
        if not self.allowed:
            raise PermissionError
        return ProductOwnerAuthorizationEvidence(
            "policy-decision", principal.principal_id, operation, context.task_id,
            context.repository_identity, context.policy_version, at, at + timedelta(minutes=5),
        )


def confirmed(root, repository, store, operation, reason=None, authorizer=None):
    issuer = ApprovalContextIssuer(
        repository, store, policy_version="policy-v1", clock=lambda: NOW,
        nonce_factory=lambda: NONCE,
    )
    challenge = issuer.issue()
    authorization = authorizer or Authorizer()
    result = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=authorization,
        context_validator=issuer.revalidate, clock=lambda: NOW,
    ).confirm(ProductOwnerConfirmationCommand(
        challenge.approval_context.approval_context_id, challenge.nonce,
        operation, reason, "command-1", "chat-client", "trusted-oidc-confirmation",
    ))
    assert result.status is ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION
    return result, authorization


@pytest.mark.parametrize("operation,target", (
    (ProductOwnerOperation.ACCEPT, AIDPState.DONE),
    (ProductOwnerOperation.REQUEST_REWORK, AIDPState.PRODUCT_OWNER_REWORK_REQUESTED),
))
def test_exact_product_owner_transition_is_consumed_once(tmp_path, operation, target):
    root, repository, store, product_commit = fixture(tmp_path)
    pending, authorizer = confirmed(
        root, repository, store, operation,
        "The risk explanation is misleading" if operation is ProductOwnerOperation.REQUEST_REWORK else None,
    )
    consumer = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW,
    )
    applied = consumer.consume()
    assert applied is not None and applied.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
    assert applied.lifecycle_state is target
    assert git(root, "rev-parse", "HEAD^") == product_commit
    assert repository.inspect().state is target
    assert consumer.consume() is None
    assert len(store.product_owner_decision_events(pending.decision_id)) == 2


def test_authorization_revocation_before_consumption_is_rejected(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    pending, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)
    authorizer.allowed = False
    result = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result is not None and result.status is ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED
    assert repository.inspect().state is AIDPState.WAITING_FOR_PRODUCT_OWNER
    assert store.product_owner_decision_events(pending.decision_id)[-1].current_state.value == "REJECTED"


def test_only_one_active_context_is_issued_for_lifecycle_binding(tmp_path):
    _, repository, store, _ = fixture(tmp_path)
    issuer = ApprovalContextIssuer(
        repository, store, policy_version="policy-v1", clock=lambda: NOW,
        nonce_factory=lambda: NONCE,
    )
    issuer.issue()
    with pytest.raises(ValueError, match="active approval context"):
        issuer.issue()


def test_head_substitution_after_confirmation_is_stale(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    pending, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)
    (root / "unrelated.txt").write_text("change\n", encoding="utf-8")
    git(root, "add", "unrelated.txt")
    git(root, "commit", "-q", "-m", "substitution")
    result = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result is not None and result.status is ProductOwnerAcceptanceStatus.REJECTED_STALE
    assert store.product_owner_decision_events(pending.decision_id)[-1].current_state.value == "STALE"


def test_head_substitution_before_confirmation_is_rejected_without_decision(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    issuer = ApprovalContextIssuer(
        repository, store, policy_version="policy-v1", clock=lambda: NOW,
        nonce_factory=lambda: NONCE,
    )
    challenge = issuer.issue()
    (root / "unrelated.txt").write_text("change\n", encoding="utf-8")
    git(root, "add", "unrelated.txt")
    git(root, "commit", "-q", "-m", "substitution before confirmation")
    result = ProductOwnerConfirmationService(
        store, authenticator=Authenticator(), authorizer=Authorizer(),
        context_validator=issuer.revalidate, clock=lambda: NOW,
    ).confirm(ProductOwnerConfirmationCommand(
        challenge.approval_context.approval_context_id, challenge.nonce,
        ProductOwnerOperation.ACCEPT, None, "command-1", "chat-client",
        "trusted-oidc-confirmation",
    ))
    assert result.status is ProductOwnerAcceptanceStatus.REJECTED_STALE
    assert store.product_owner_decisions() == ()


def test_repository_and_policy_substitution_are_stale(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    _, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)
    git(root, "remote", "set-url", "origin", str(tmp_path / "substituted.git"))
    result = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="substituted-policy", clock=lambda: NOW,
    ).consume()
    assert result.status is ProductOwnerAcceptanceStatus.REJECTED_STALE
    assert repository.inspect().state is AIDPState.WAITING_FOR_PRODUCT_OWNER


def test_concurrent_consumers_apply_at_most_once(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    _, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)
    barrier = threading.Barrier(2)
    results = []

    def consume():
        consumer = ProductOwnerDecisionConsumer(
            repository, store, LifecycleProjection(root), authorizer=authorizer,
            policy_version="policy-v1", clock=lambda: NOW,
        )
        barrier.wait()
        results.append(consumer.consume())

    threads = (threading.Thread(target=consume), threading.Thread(target=consume))
    for thread in threads: thread.start()
    for thread in threads: thread.join(timeout=10)
    assert all(not thread.is_alive() for thread in threads)
    assert sum(
        result is not None and result.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
        for result in results
    ) == 1
    assert repository.inspect().state is AIDPState.DONE


def test_push_failure_recovers_exact_committed_projection(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    pending, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)

    class FailingPushProjection(LifecycleProjection):
        def push(self, expected_branch):
            raise RuntimeError("simulated upstream failure")

    first = ProductOwnerDecisionConsumer(
        repository, store, FailingPushProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert first.status is ProductOwnerAcceptanceStatus.BLOCKED
    assert store.product_owner_transaction(pending.decision_id)[-1]["state"] == "COMMITTED"
    recovered = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW + timedelta(hours=1),
    ).consume()
    assert recovered.status is ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED
    assert repository.inspect().state is AIDPState.DONE


def test_replacement_architect_result_invalidates_confirmed_decision(tmp_path):
    root, repository, store, _ = fixture(tmp_path)
    _, authorizer = confirmed(root, repository, store, ProductOwnerOperation.ACCEPT)
    replacement = create_review_result(
        review_request_id="7" * 64, task_id="TASK-0131", execution_id="replacement-execution",
        review_iteration=1, disposition=ArchitectReviewDisposition.PASS,
        reviewed_head="8" * 40, expected_head="9" * 40, reviewed_tree_hash="a" * 40,
        findings=(), allowed_rework_scope=(), required_validations=(),
        provenance=ArchitectReviewProvenance("process", "launcher", "model", NOW, NOW, "v1"),
        failure_reason=None, authority_claims=(), created_at=NOW,
    )
    store.persist_architect_result(replacement)
    result = ProductOwnerDecisionConsumer(
        repository, store, LifecycleProjection(root), authorizer=authorizer,
        policy_version="policy-v1", clock=lambda: NOW,
    ).consume()
    assert result.status is ProductOwnerAcceptanceStatus.REJECTED_STALE
    assert repository.inspect().state is AIDPState.WAITING_FOR_PRODUCT_OWNER
