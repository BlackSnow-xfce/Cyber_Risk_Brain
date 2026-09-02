"""Trusted core boundary for Product Owner transaction confirmation.

No transport or identity-provider adapter lives here.  Callers must provide
independently verified authentication and authorization implementations.
"""

from __future__ import annotations

import hashlib
import secrets
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Protocol

from .contracts import (
    AIDPState,
    ArchitectReviewDisposition,
    AuthenticatedProductOwner,
    ProductOwnerAcceptanceResult,
    ProductOwnerAcceptanceStatus,
    ProductOwnerApprovalContext,
    ProductOwnerAuthorizationEvidence,
    ProductOwnerDecision,
    ProductOwnerDecisionEvent,
    ProductOwnerDecisionState,
    ProductOwnerOperation,
    canonical_digest,
    utc_now,
)
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore
from .watcher_runtime import WatcherRuntimeLock


@dataclass(frozen=True, slots=True)
class ApprovalChallenge:
    approval_context: ProductOwnerApprovalContext
    nonce: str


@dataclass(frozen=True, slots=True)
class ProductOwnerConfirmationCommand:
    approval_context_id: str
    nonce: str
    operation: ProductOwnerOperation
    reason: str | None
    command_id: str
    client_identity: str
    authentication_proof: object

    def __post_init__(self) -> None:
        if len(self.approval_context_id) != 64 or any(character not in "0123456789abcdef" for character in self.approval_context_id):
            raise ValueError("approval_context_id must be a lowercase SHA-256 identity")
        for name in ("nonce", "command_id", "client_identity"):
            value = getattr(self, name)
            if not value.strip() or len(value) > 256 or "\n" in value or "\r" in value:
                raise ValueError(f"{name} must be explicit, single-line and bounded")
        if self.reason is not None and (not self.reason.strip() or len(self.reason) > 2048):
            raise ValueError("reason must be non-empty and bounded")
        if self.operation is ProductOwnerOperation.REQUEST_REWORK and self.reason is None:
            raise ValueError("REQUEST_REWORK requires a reason")


class ProductOwnerAuthenticator(Protocol):
    def authenticate(
        self, proof: object, context: ProductOwnerApprovalContext,
    ) -> AuthenticatedProductOwner: ...


class ProductOwnerAuthorizer(Protocol):
    def authorize(
        self,
        principal: AuthenticatedProductOwner,
        context: ProductOwnerApprovalContext,
        operation: ProductOwnerOperation,
        *,
        at: datetime,
    ) -> ProductOwnerAuthorizationEvidence: ...


class ApprovalContextValidator(Protocol):
    def __call__(self, context: ProductOwnerApprovalContext, *, at: datetime) -> None: ...


class ApprovalContextIssuer:
    def __init__(
        self,
        repository: AIDPRepository,
        runtime: LocalRuntimeStore,
        *,
        policy_version: str,
        lifetime: timedelta = timedelta(minutes=10),
        clock: Callable[[], datetime] = utc_now,
        nonce_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
        lock: WatcherRuntimeLock | None = None,
    ) -> None:
        if not policy_version.strip() or lifetime <= timedelta(0) or lifetime > timedelta(hours=1):
            raise ValueError("approval context policy and lifetime must be explicit and bounded")
        self.repository = repository
        self.runtime = runtime
        self.policy_version = policy_version
        self.lifetime = lifetime
        self.clock = clock
        self.nonce_factory = nonce_factory
        self.lock = lock or WatcherRuntimeLock(runtime.root / "product-owner-context-issuance.lock")

    def revalidate(self, context: ProductOwnerApprovalContext, *, at: datetime) -> None:
        decision = self.repository.inspect()
        result = self.runtime.latest_architect_result(context.task_id)
        repository_identity, remote_identity = _repository_identities(self.repository.root)
        if result is None:
            raise RuntimeError("Architect result is unavailable")
        lifecycle_version = canonical_digest({
            "task_id": decision.task_id, "state": decision.state, "commit": decision.commit,
            "execution_id": result.execution_id, "review_result_id": result.review_result_id,
        })
        if (
            at >= context.expires_at
            or decision.task_id != context.task_id
            or decision.state is not context.expected_state
            or decision.commit != context.product_commit
            or repository_identity != context.repository_identity
            or remote_identity != context.repository_remote_identity
            or lifecycle_version != context.expected_lifecycle_version
            or result.execution_id != context.implementation_execution_id
            or result.review_result_id != context.architect_review_id
            or canonical_digest({"architect_review_result": result}) != context.architect_result_digest
        ):
            raise ValueError("approval context is stale")

    def issue(self) -> ApprovalChallenge:
        if not self.lock.acquire():
            raise RuntimeError("approval context issuance lock is unavailable")
        try:
            return self._issue_locked()
        finally:
            self.lock.release()

    def _issue_locked(self) -> ApprovalChallenge:
        decision = self.repository.inspect()
        if decision.state is not AIDPState.WAITING_FOR_PRODUCT_OWNER or decision.task_id is None:
            raise ValueError("approval context requires WAITING_FOR_PRODUCT_OWNER")
        result = self.runtime.latest_architect_result(decision.task_id)
        if result is None or result.disposition is not ArchitectReviewDisposition.PASS:
            raise ValueError("approval context requires one authoritative Architect PASS")
        # The Architect projection commit is the current product commit; the
        # reviewed expected HEAD must be its exact parent.
        parent = self.repository._git("rev-parse", f"{decision.commit}^")
        if parent != result.expected_head:
            raise ValueError("Architect result does not bind current product commit")
        now = self.clock()
        nonce = self.nonce_factory()
        if len(nonce) < 32 or "\n" in nonce or "\r" in nonce:
            raise ValueError("nonce factory returned an unsafe nonce")
        nonce_digest = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
        repository_identity, remote_identity = _repository_identities(self.repository.root)
        lifecycle_version = canonical_digest({
            "task_id": decision.task_id,
            "state": decision.state,
            "commit": decision.commit,
            "execution_id": result.execution_id,
            "review_result_id": result.review_result_id,
        })
        active = tuple(
            item for item in self.runtime.product_owner_approval_contexts()
            if item.task_id == decision.task_id
            and item.expected_lifecycle_version == lifecycle_version
            and now < item.expires_at
        )
        if active:
            raise ValueError("an active approval context already exists for this lifecycle binding")
        values = dict(
            schema_version="product-owner-approval-context-v1",
            task_id=decision.task_id,
            repository_identity=repository_identity,
            repository_remote_identity=remote_identity,
            expected_state=AIDPState.WAITING_FOR_PRODUCT_OWNER,
            expected_lifecycle_version=lifecycle_version,
            policy_version=self.policy_version,
            implementation_execution_id=result.execution_id,
            architect_review_id=result.review_result_id,
            architect_result_digest=canonical_digest({"architect_review_result": result}),
            product_commit=decision.commit,
            issued_at=now,
            expires_at=now + self.lifetime,
            nonce_digest=nonce_digest,
        )
        identity = canonical_digest(values)
        context = ProductOwnerApprovalContext(
            approval_context_id=identity, context_digest=identity, **values,
        )
        self.runtime.persist_product_owner_approval_context(context)
        return ApprovalChallenge(context, nonce)


class ProductOwnerConfirmationService:
    def __init__(
        self,
        runtime: LocalRuntimeStore,
        *,
        authenticator: ProductOwnerAuthenticator | None,
        authorizer: ProductOwnerAuthorizer | None,
        context_validator: ApprovalContextValidator | None = None,
        clock: Callable[[], datetime] = utc_now,
        lock: WatcherRuntimeLock | None = None,
    ) -> None:
        self.runtime = runtime
        self.authenticator = authenticator
        self.authorizer = authorizer
        self.context_validator = context_validator
        self.clock = clock
        self.lock = lock or WatcherRuntimeLock(runtime.root / "product-owner-confirmation.lock")

    def confirm(self, command: ProductOwnerConfirmationCommand) -> ProductOwnerAcceptanceResult:
        try:
            if not self.lock.acquire():
                return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "confirmation_lock_unavailable")
        except (OSError, RuntimeError, ValueError):
            return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "confirmation_lock_failed")
        try:
            return self._confirm_locked(command)
        finally:
            self.lock.release()

    def _confirm_locked(self, command: ProductOwnerConfirmationCommand) -> ProductOwnerAcceptanceResult:
        if self.authenticator is None or self.authorizer is None or self.context_validator is None:
            return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "trusted_identity_boundary_unavailable")
        try:
            context = self.runtime.product_owner_approval_context(command.approval_context_id)
        except (OSError, RuntimeError):
            return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "approval_context_unavailable")
        except ValueError:
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "approval_context_invalid")
        now = self.clock()
        if now >= context.expires_at:
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_STALE, "approval_context_expired")
        nonce_digest = hashlib.sha256(command.nonce.encode("utf-8")).hexdigest()
        if not secrets.compare_digest(nonce_digest, context.nonce_digest):
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "nonce_invalid")
        try:
            self.context_validator(context, at=now)
            principal = self.authenticator.authenticate(command.authentication_proof, context)
            confirmed_at = self.clock()
            if confirmed_at >= context.expires_at:
                return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_STALE, "approval_context_expired")
            self.context_validator(context, at=confirmed_at)
            authorization = self.authorizer.authorize(principal, context, command.operation, at=confirmed_at)
            _validate_authorization(authorization, principal, context, command.operation, confirmed_at)
            payload_digest = canonical_digest({
                "approval_context_id": command.approval_context_id,
                "operation": command.operation,
                "reason": command.reason,
                "client_identity": command.client_identity,
            })
            nonce_decisions = tuple(
                item for item in self.runtime.product_owner_decisions()
                if item.nonce_digest == nonce_digest
            )
            if nonce_decisions:
                existing = nonce_decisions[0]
                if len(nonce_decisions) != 1 or existing.command_id != command.command_id or existing.command_payload_digest != payload_digest:
                    return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "nonce_already_used")
                existing_events = self.runtime.product_owner_decision_events(existing.decision_id)
                if not existing_events:
                    return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "partial_decision_persistence")
                terminal = existing_events[-1].current_state
                if terminal is ProductOwnerDecisionState.CONSUMED:
                    target = (
                        AIDPState.DONE if existing.operation is ProductOwnerOperation.ACCEPT
                        else AIDPState.PRODUCT_OWNER_REWORK_REQUESTED
                    )
                    return ProductOwnerAcceptanceResult(
                        ProductOwnerAcceptanceStatus.ALREADY_APPLIED,
                        context.task_id, context.approval_context_id, existing.decision_id,
                        existing.operation, target, "decision_already_consumed",
                        existing.decided_at, existing_events[-1].timestamp,
                    )
                if terminal in {ProductOwnerDecisionState.STALE, ProductOwnerDecisionState.REJECTED}:
                    status = (
                        ProductOwnerAcceptanceStatus.REJECTED_STALE
                        if terminal is ProductOwnerDecisionState.STALE
                        else ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED
                    )
                    return ProductOwnerAcceptanceResult(
                        status, context.task_id, context.approval_context_id,
                        existing.decision_id, existing.operation,
                        AIDPState.WAITING_FOR_PRODUCT_OWNER,
                        existing_events[-1].reason_code, existing.decided_at,
                    )
                return ProductOwnerAcceptanceResult(
                    ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION,
                    context.task_id, context.approval_context_id, existing.decision_id,
                    existing.operation, AIDPState.WAITING_FOR_PRODUCT_OWNER,
                    "idempotent_replay", existing.decided_at,
                )
            replay = self.runtime.product_owner_idempotency(
                principal.principal_id, command.command_id,
            )
            if replay is not None:
                if replay[0] != payload_digest:
                    return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "idempotency_payload_mismatch")
                existing = self.runtime.product_owner_decision(replay[1])
                return ProductOwnerAcceptanceResult(
                    ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION,
                    context.task_id, context.approval_context_id, existing.decision_id,
                    existing.operation, AIDPState.WAITING_FOR_PRODUCT_OWNER,
                    "idempotent_replay", existing.decided_at,
                )
            values = dict(
                schema_version="product-owner-decision-v1",
                approval_context_id=context.approval_context_id,
                approval_context_digest=context.context_digest,
                principal=principal,
                authorization=authorization,
                operation=command.operation,
                reason=command.reason,
                decided_at=confirmed_at,
                client_identity=command.client_identity,
                command_id=command.command_id,
                command_payload_digest=payload_digest,
                nonce_digest=nonce_digest,
            )
            identity = canonical_digest(values)
            decision = ProductOwnerDecision(
                decision_id=identity, integrity_digest=identity, **values,
            )
            self.runtime.persist_product_owner_decision(decision)
            event = _event(decision, None, ProductOwnerDecisionState.RECORDED, "confirmed", confirmed_at, None)
            self.runtime.append_product_owner_decision_event(event)
            self.runtime.persist_product_owner_idempotency(
                principal.principal_id, command.command_id, payload_digest, decision.decision_id,
            )
        except PermissionError:
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_UNAUTHORIZED, "product_owner_unauthorized")
        except (OSError, RuntimeError):
            return self._reject(command, ProductOwnerAcceptanceStatus.BLOCKED, "confirmation_dependency_unavailable")
        except ValueError as error:
            if str(error) == "approval context is stale":
                return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_STALE, "approval_context_stale")
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "confirmation_rejected")
        except TypeError:
            return self._reject(command, ProductOwnerAcceptanceStatus.REJECTED_INVALID_REQUEST, "confirmation_rejected")
        return ProductOwnerAcceptanceResult(
            ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION,
            context.task_id, context.approval_context_id, decision.decision_id,
            decision.operation, AIDPState.WAITING_FOR_PRODUCT_OWNER,
            "decision_recorded", decision.decided_at,
        )

    def _reject(
        self,
        command: ProductOwnerConfirmationCommand,
        status: ProductOwnerAcceptanceStatus,
        reason: str,
    ) -> ProductOwnerAcceptanceResult:
        try:
            self.runtime.append_product_owner_confirmation_attempt({
                "approval_context_id": command.approval_context_id,
                "command_identity_digest": canonical_digest(command.command_id),
                "client_identity_digest": canonical_digest(command.client_identity),
                "operation": command.operation,
                "status": status,
                "reason_code": reason,
                "timestamp": self.clock(),
            })
        except (OSError, RuntimeError, TypeError, ValueError):
            return _rejected(command, ProductOwnerAcceptanceStatus.BLOCKED, "rejection_audit_unavailable")
        return _rejected(command, status, reason)


def create_decision_event(
    decision: ProductOwnerDecision,
    state: ProductOwnerDecisionState,
    reason_code: str,
    timestamp: datetime,
    previous_event: ProductOwnerDecisionEvent,
) -> ProductOwnerDecisionEvent:
    return _event(decision, previous_event.current_state, state, reason_code, timestamp, previous_event.event_digest)


def create_recorded_decision_event(
    decision: ProductOwnerDecision, timestamp: datetime,
) -> ProductOwnerDecisionEvent:
    return _event(decision, None, ProductOwnerDecisionState.RECORDED, "confirmed", timestamp, None)


def _event(
    decision: ProductOwnerDecision,
    previous: ProductOwnerDecisionState | None,
    current: ProductOwnerDecisionState,
    reason: str,
    timestamp: datetime,
    previous_digest: str | None,
) -> ProductOwnerDecisionEvent:
    values = dict(
        decision_id=decision.decision_id,
        approval_context_id=decision.approval_context_id,
        previous_state=previous,
        current_state=current,
        event_type=f"PRODUCT_OWNER_DECISION_{current.value}",
        binding_digest=decision.approval_context_digest,
        timestamp=timestamp,
        reason_code=reason,
        previous_event_digest=previous_digest,
    )
    identity = canonical_digest(values)
    return ProductOwnerDecisionEvent(event_id=identity, event_digest=identity, **values)


def _validate_authorization(
    authorization: ProductOwnerAuthorizationEvidence,
    principal: AuthenticatedProductOwner,
    context: ProductOwnerApprovalContext,
    operation: ProductOwnerOperation,
    now: datetime,
) -> None:
    if (
        authorization.principal_id != principal.principal_id
        or authorization.operation is not operation
        or authorization.task_id != context.task_id
        or authorization.repository_identity != context.repository_identity
        or authorization.policy_version != context.policy_version
        or authorization.evaluated_at > now
        or (authorization.valid_until is not None and now >= authorization.valid_until)
    ):
        raise PermissionError("Product Owner authorization does not bind the approval context")


def _repository_identities(root: Path) -> tuple[str, str]:
    common = subprocess.check_output(
        ("git", "rev-parse", "--git-common-dir"), cwd=root, text=True,
    ).strip()
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = root / common_path
    remote = subprocess.check_output(
        ("git", "remote", "get-url", "origin"), cwd=root, text=True,
    ).strip()
    return canonical_digest({"root": str(root.resolve()), "git_common_dir": str(common_path.resolve())}), remote


def _rejected(
    command: ProductOwnerConfirmationCommand,
    status: ProductOwnerAcceptanceStatus,
    reason: str,
) -> ProductOwnerAcceptanceResult:
    return ProductOwnerAcceptanceResult(
        status, "UNKNOWN", command.approval_context_id, None, command.operation,
        AIDPState.WAITING_FOR_PRODUCT_OWNER, reason,
    )
