from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import StrEnum

from core.incident_response._validation import required
from core.incident_response.context import (
    IncidentLifecycleStatus,
    IncidentPrincipalReference,
    SecurityIncidentContext,
)


class IncidentTransitionValidationStatus(StrEnum):
    ALLOWED = "allowed"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class IncidentLifecycleTransitionRequest:
    incident_id: str
    expected_status: IncidentLifecycleStatus
    target_status: IncidentLifecycleStatus
    actor: IncidentPrincipalReference
    occurred_at: datetime
    justification: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "incident_id",
            required(self.incident_id, "Incident ID"),
        )
        if not isinstance(self.expected_status, IncidentLifecycleStatus):
            raise ValueError("Expected incident status must be canonical.")
        if not isinstance(self.target_status, IncidentLifecycleStatus):
            raise ValueError("Target incident status must be canonical.")
        if not isinstance(self.actor, IncidentPrincipalReference):
            raise ValueError("Transition actor must be a principal reference.")
        if not isinstance(self.occurred_at, datetime):
            raise ValueError("Transition timestamp must be a datetime.")
        if self.occurred_at.utcoffset() is None:
            raise ValueError("Transition timestamp must be timezone-aware.")
        if self.occurred_at.utcoffset() != timedelta(0):
            raise ValueError("Transition timestamp must be UTC.")
        object.__setattr__(
            self,
            "justification",
            required(self.justification, "Transition justification"),
        )


@dataclass(frozen=True, slots=True)
class IncidentLifecycleTransitionResult:
    status: IncidentTransitionValidationStatus
    incident_id: str
    from_status: IncidentLifecycleStatus
    to_status: IncidentLifecycleStatus
    reason: str
    resulting_context: SecurityIncidentContext | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, IncidentTransitionValidationStatus):
            raise ValueError("Transition validation status must be canonical.")
        object.__setattr__(
            self,
            "incident_id",
            required(self.incident_id, "Incident ID"),
        )
        if not isinstance(self.from_status, IncidentLifecycleStatus):
            raise ValueError("Transition source status must be canonical.")
        if not isinstance(self.to_status, IncidentLifecycleStatus):
            raise ValueError("Transition target status must be canonical.")
        object.__setattr__(self, "reason", required(self.reason, "Transition result reason"))
        if self.status is IncidentTransitionValidationStatus.ALLOWED:
            if self.resulting_context is None:
                raise ValueError("Allowed transitions require a resulting context.")
        elif self.resulting_context is not None:
            raise ValueError("Invalid transitions must not expose a resulting context.")

    @property
    def allowed(self) -> bool:
        return self.status is IncidentTransitionValidationStatus.ALLOWED


class IncidentLifecycleTransitionService:
    """Evaluate incident lifecycle transitions without persistence or authorization."""

    _ALLOWED_TRANSITIONS = frozenset(
        {
            (IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.INVESTIGATING),
            (IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.CLOSED),
            (
                IncidentLifecycleStatus.INVESTIGATING,
                IncidentLifecycleStatus.RESOLVED,
            ),
            (IncidentLifecycleStatus.RESOLVED, IncidentLifecycleStatus.INVESTIGATING),
            (IncidentLifecycleStatus.RESOLVED, IncidentLifecycleStatus.CLOSED),
            (IncidentLifecycleStatus.CLOSED, IncidentLifecycleStatus.INVESTIGATING),
        }
    )

    def evaluate(
        self,
        context: SecurityIncidentContext,
        request: IncidentLifecycleTransitionRequest,
    ) -> IncidentLifecycleTransitionResult:
        if not isinstance(context, SecurityIncidentContext):
            raise ValueError("Lifecycle transitions require a security incident context.")
        if request.incident_id != context.incident_id:
            return self._invalid(context, "Transition incident ID does not match context.")
        if request.expected_status is not context.lifecycle_status:
            return self._invalid(context, "Expected incident status does not match context.")
        if (context.lifecycle_status, request.target_status) not in self._ALLOWED_TRANSITIONS:
            return self._invalid(context, "Incident lifecycle transition is not allowed.")
        if request.occurred_at < context.created_at:
            return self._invalid(context, "Transition timestamp precedes incident creation.")
        if request.occurred_at < context.updated_at:
            return self._invalid(context, "Transition timestamp precedes incident update.")

        resulting_context = replace(
            context,
            lifecycle_status=request.target_status,
            updated_at=request.occurred_at,
        )
        return IncidentLifecycleTransitionResult(
            status=IncidentTransitionValidationStatus.ALLOWED,
            incident_id=context.incident_id,
            from_status=context.lifecycle_status,
            to_status=request.target_status,
            reason="Incident lifecycle transition is allowed.",
            resulting_context=resulting_context,
        )

    @staticmethod
    def _invalid(
        context: SecurityIncidentContext,
        reason: str,
    ) -> IncidentLifecycleTransitionResult:
        return IncidentLifecycleTransitionResult(
            status=IncidentTransitionValidationStatus.INVALID,
            incident_id=context.incident_id,
            from_status=context.lifecycle_status,
            to_status=context.lifecycle_status,
            reason=reason,
        )

