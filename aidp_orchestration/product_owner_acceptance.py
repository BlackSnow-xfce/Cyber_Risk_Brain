"""Fail-closed consumption of independently confirmed Product Owner decisions."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .contracts import (
    AIDPState,
    ArchitectReviewDisposition,
    ProductOwnerAcceptanceResult,
    ProductOwnerAcceptanceStatus,
    ProductOwnerDecision,
    ProductOwnerDecisionState,
    ProductOwnerOperation,
    canonical_digest,
    utc_now,
)
from .lifecycle_projection import LifecycleProjection
from .product_owner_confirmation import (
    ProductOwnerAuthorizer,
    _repository_identities,
    _validate_authorization,
    create_decision_event,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .watcher_runtime import WatcherRuntimeLock


class StaleProductOwnerApprovalError(ValueError):
    pass


class ProductOwnerStatusProjector:
    """Safe read model; it carries no lifecycle authority."""

    def __init__(self, runtime: LocalRuntimeStore) -> None:
        self.runtime = runtime

    def project(self, decision_id: str) -> ProductOwnerAcceptanceResult:
        decision = self.runtime.product_owner_decision(decision_id)
        events = self.runtime.product_owner_decision_events(decision_id)
        if not events:
            return ProductOwnerDecisionConsumer._result(
                decision, ProductOwnerAcceptanceStatus.BLOCKED, "decision_journal_incomplete",
            )
        state = events[-1].current_state
        statuses = {
            ProductOwnerDecisionState.RECORDED: ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION,
            ProductOwnerDecisionState.CONSUMED: ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED,
            ProductOwnerDecisionState.STALE: ProductOwnerAcceptanceStatus.REJECTED_STALE,
            ProductOwnerDecisionState.REJECTED: ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED,
        }
        result = ProductOwnerDecisionConsumer._result(
            decision, statuses[state], events[-1].reason_code,
        )
        if state is ProductOwnerDecisionState.CONSUMED:
            return ProductOwnerAcceptanceResult(
                result.status, result.task_id, result.approval_context_id,
                result.decision_id, result.operation, result.lifecycle_state,
                result.reason_code, result.recorded_at, events[-1].timestamp,
            )
        return result


class ProductOwnerDecisionConsumer:
    def __init__(
        self,
        repository: AIDPRepository,
        runtime: LocalRuntimeStore,
        projection: LifecycleProjection,
        *,
        authorizer: ProductOwnerAuthorizer | None,
        policy_version: str,
        clock: Callable[[], datetime] = utc_now,
        lock: WatcherRuntimeLock | None = None,
    ) -> None:
        if not policy_version.strip():
            raise ValueError("Product Owner lifecycle policy version is required")
        self.repository = repository
        self.runtime = runtime
        self.projection = projection
        self.authorizer = authorizer
        self.policy_version = policy_version
        self.clock = clock
        self.lock = lock or WatcherRuntimeLock(
            runtime.root / "product-owner-consumption.lock",
        )

    def consume(self) -> ProductOwnerAcceptanceResult | None:
        try:
            pending = self.runtime.recorded_product_owner_decisions()
        except (OSError, RuntimeError, TypeError, ValueError):
            return ProductOwnerAcceptanceResult(
                ProductOwnerAcceptanceStatus.BLOCKED, "UNKNOWN", "0" * 64,
                None, None, AIDPState.WAITING_FOR_PRODUCT_OWNER,
                "decision_journal_unavailable",
            )
        if not pending:
            return None
        if len(pending) != 1:
            decision = pending[0]
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "ambiguous_pending_decisions")
        decision = pending[0]
        if self.authorizer is None:
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "authorization_boundary_unavailable")
        try:
            if not self.lock.acquire():
                return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "consumption_lock_unavailable")
        except (OSError, RuntimeError, ValueError):
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "consumption_lock_failed")
        try:
            try:
                return self._consume_locked(decision)
            except (OSError, RuntimeError, TypeError, ValueError):
                return self._result(
                    decision, ProductOwnerAcceptanceStatus.BLOCKED,
                    "decision_consumption_integrity_failure",
                )
        finally:
            self.lock.release()

    def _consume_locked(self, decision: ProductOwnerDecision) -> ProductOwnerAcceptanceResult:
        events = self.runtime.product_owner_decision_events(decision.decision_id)
        if len(events) != 1 or events[0].current_state is not ProductOwnerDecisionState.RECORDED:
            if events and events[-1].current_state is ProductOwnerDecisionState.CONSUMED:
                return self._result(decision, ProductOwnerAcceptanceStatus.ALREADY_APPLIED, "decision_already_consumed")
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "decision_journal_invalid")
        recorded = events[0]
        if (
            recorded.decision_id != decision.decision_id
            or recorded.approval_context_id != decision.approval_context_id
            or recorded.binding_digest != decision.approval_context_digest
        ):
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "decision_journal_binding_invalid")
        context = self.runtime.product_owner_approval_context(decision.approval_context_id)
        now = self.clock()
        transaction = self.runtime.product_owner_transaction(decision.decision_id)
        if any(
            item.get("approval_context_id") != decision.approval_context_id
            or item.get("binding_digest") != decision.approval_context_digest
            or item.get("operation") != decision.operation.value
            for item in transaction
        ):
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "transaction_binding_invalid")
        recovering = bool(transaction) and self.repository.head != context.product_commit
        try:
            if recovering:
                parent = self.repository._git("rev-parse", f"{self.repository.head}^")
                if parent != context.product_commit:
                    raise ValueError("recovery commit does not bind approved product commit")
                self.projection.verify_product_owner_projection(decision, self.repository.head)
            else:
                self._validate_binding(decision, now)
                authorization = self.authorizer.authorize(
                    decision.principal, context, decision.operation, at=now,
                )
                _validate_authorization(authorization, decision.principal, context, decision.operation, now)
        except PermissionError:
            terminal = create_decision_event(
                decision, ProductOwnerDecisionState.REJECTED,
                "authorization_revoked", now, recorded,
            )
            self.runtime.append_product_owner_decision_event(terminal)
            return self._result(decision, ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED, "authorization_revoked")
        except StaleProductOwnerApprovalError:
            terminal = create_decision_event(
                decision, ProductOwnerDecisionState.STALE,
                "approval_binding_stale", now, recorded,
            )
            self.runtime.append_product_owner_decision_event(terminal)
            return self._result(decision, ProductOwnerAcceptanceStatus.REJECTED_STALE, "approval_binding_stale")
        except (OSError, RuntimeError, TypeError, ValueError):
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "binding_verification_unavailable")

        try:
            if not transaction:
                self.runtime.append_product_owner_transaction(
                    decision.decision_id, self._transaction(decision, "INTENT", now),
                )
                transaction = self.runtime.product_owner_transaction(decision.decision_id)
            head = self.repository.head
            if head == context.product_commit:
                projected_head = self.projection.project_product_owner_decision(decision)
            else:
                projected_head = head
                parent = self.repository._git("rev-parse", f"{projected_head}^")
                if parent != context.product_commit:
                    raise RuntimeError("pending Product Owner projection parent is stale")
                self.projection.verify_product_owner_projection(decision, projected_head)
            latest_state = str(transaction[-1].get("state", ""))
            if latest_state == "INTENT":
                self.runtime.append_product_owner_transaction(
                    decision.decision_id,
                    self._transaction(decision, "COMMITTED", self.clock(), projected_head, transaction[-1]),
                )
            self.projection.verify_product_owner_projection(decision, projected_head)
            transaction = self.runtime.product_owner_transaction(decision.decision_id)
            if str(transaction[-1].get("state", "")) != "PUBLISHED":
                self.projection.push(self.repository.branch)
                transaction = self.runtime.product_owner_transaction(decision.decision_id)
                self.runtime.append_product_owner_transaction(
                    decision.decision_id,
                    self._transaction(decision, "PUBLISHED", self.clock(), projected_head, transaction[-1]),
                )
            terminal = create_decision_event(
                decision, ProductOwnerDecisionState.CONSUMED,
                "decision_applied", self.clock(), recorded,
            )
            self.runtime.append_product_owner_decision_event(terminal)
        except (OSError, RuntimeError, TypeError, ValueError):
            return self._result(decision, ProductOwnerAcceptanceStatus.BLOCKED, "atomic_consumption_incomplete")
        target = (
            AIDPState.DONE if decision.operation is ProductOwnerOperation.ACCEPT
            else AIDPState.PRODUCT_OWNER_REWORK_REQUESTED
        )
        return ProductOwnerAcceptanceResult(
            ProductOwnerAcceptanceStatus.ACCEPTED_AND_APPLIED,
            context.task_id, context.approval_context_id, decision.decision_id,
            decision.operation, target, "decision_applied", decision.decided_at,
            terminal.timestamp,
        )

    def _validate_binding(self, decision: ProductOwnerDecision, now: datetime) -> None:
        context = self.runtime.product_owner_approval_context(decision.approval_context_id)
        repository_decision = self.repository.inspect()
        result = self.runtime.latest_architect_result(context.task_id)
        repository_identity, remote_identity = _repository_identities(self.repository.root)
        if result is None:
            raise ValueError("Architect result is missing")
        lifecycle_version = canonical_digest({
            "task_id": repository_decision.task_id,
            "state": repository_decision.state,
            "commit": repository_decision.commit,
            "execution_id": result.execution_id,
            "review_result_id": result.review_result_id,
        })
        if (
            now >= context.expires_at
            or decision.approval_context_digest != context.context_digest
            or decision.nonce_digest != context.nonce_digest
            or repository_decision.task_id != context.task_id
            or repository_decision.state is not AIDPState.WAITING_FOR_PRODUCT_OWNER
            or repository_decision.commit != context.product_commit
            or repository_identity != context.repository_identity
            or remote_identity != context.repository_remote_identity
            or lifecycle_version != context.expected_lifecycle_version
            or context.policy_version != self.policy_version
            or result.disposition is not ArchitectReviewDisposition.PASS
            or result.execution_id != context.implementation_execution_id
            or result.review_result_id != context.architect_review_id
            or canonical_digest({"architect_review_result": result}) != context.architect_result_digest
        ):
            raise StaleProductOwnerApprovalError("Product Owner decision binding is stale")

    @staticmethod
    def _transaction(
        decision: ProductOwnerDecision, state: str, timestamp: datetime,
        projection_commit: str | None = None,
        previous: dict[str, object] | None = None,
    ) -> dict[str, object]:
        values = {
            "schema_version": "product-owner-transaction-v1",
            "decision_id": decision.decision_id,
            "approval_context_id": decision.approval_context_id,
            "binding_digest": decision.approval_context_digest,
            "operation": decision.operation,
            "state": state,
            "timestamp": timestamp,
            "projection_commit": projection_commit,
            "previous_event_digest": previous.get("event_digest") if previous is not None else None,
        }
        return {**values, "event_digest": canonical_digest(values)}

    @staticmethod
    def _result(
        decision: ProductOwnerDecision,
        status: ProductOwnerAcceptanceStatus,
        reason: str,
    ) -> ProductOwnerAcceptanceResult:
        target = (
            AIDPState.DONE if decision.operation is ProductOwnerOperation.ACCEPT
            else AIDPState.PRODUCT_OWNER_REWORK_REQUESTED
        )
        return ProductOwnerAcceptanceResult(
            status, decision.authorization.task_id, decision.approval_context_id,
            decision.decision_id, decision.operation, target, reason, decision.decided_at,
        )
