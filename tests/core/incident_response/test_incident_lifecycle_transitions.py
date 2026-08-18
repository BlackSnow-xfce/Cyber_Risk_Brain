from datetime import datetime, timedelta, timezone

import pytest

from core.incident_response import (
    IncidentLifecycleStatus,
    IncidentLifecycleTransitionRequest,
    IncidentLifecycleTransitionService,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentTransitionValidationStatus,
    SecurityIncidentContext,
)


NOW = datetime(2026, 8, 18, 14, 0, tzinfo=timezone.utc)
ACTOR = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001")


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.INVESTIGATING),
        (IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.CLOSED),
        (IncidentLifecycleStatus.INVESTIGATING, IncidentLifecycleStatus.RESOLVED),
        (IncidentLifecycleStatus.RESOLVED, IncidentLifecycleStatus.INVESTIGATING),
        (IncidentLifecycleStatus.RESOLVED, IncidentLifecycleStatus.CLOSED),
        (IncidentLifecycleStatus.CLOSED, IncidentLifecycleStatus.INVESTIGATING),
    ],
)
def test_every_adr_0009_transition_is_allowed(
    source: IncidentLifecycleStatus,
    target: IncidentLifecycleStatus,
) -> None:
    context = _context(status=source)
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(source, target),
    )

    assert result.status is IncidentTransitionValidationStatus.ALLOWED
    assert result.allowed is True
    assert result.from_status is source
    assert result.to_status is target
    assert result.resulting_context is not None
    assert result.resulting_context.lifecycle_status is target
    assert result.resulting_context.updated_at == NOW


@pytest.mark.parametrize(
    ("source", "target"),
    [
        (IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.OPEN),
        (IncidentLifecycleStatus.INVESTIGATING, IncidentLifecycleStatus.OPEN),
        (IncidentLifecycleStatus.INVESTIGATING, IncidentLifecycleStatus.CLOSED),
        (IncidentLifecycleStatus.RESOLVED, IncidentLifecycleStatus.OPEN),
        (IncidentLifecycleStatus.CLOSED, IncidentLifecycleStatus.OPEN),
        (IncidentLifecycleStatus.CLOSED, IncidentLifecycleStatus.RESOLVED),
    ],
)
def test_unauthorized_lifecycle_transitions_fail_closed(
    source: IncidentLifecycleStatus,
    target: IncidentLifecycleStatus,
) -> None:
    context = _context(status=source)
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(source, target),
    )

    assert result.status is IncidentTransitionValidationStatus.INVALID
    assert result.allowed is False
    assert result.resulting_context is None
    assert result.from_status is source
    assert result.to_status is source


def test_expected_status_mismatch_fails_closed() -> None:
    context = _context(status=IncidentLifecycleStatus.OPEN)
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(IncidentLifecycleStatus.INVESTIGATING, IncidentLifecycleStatus.RESOLVED),
    )

    assert result.status is IncidentTransitionValidationStatus.INVALID
    assert "does not match" in result.reason


def test_incident_id_mismatch_fails_closed() -> None:
    context = _context()
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.CLOSED, incident_id="other"),
    )

    assert result.status is IncidentTransitionValidationStatus.INVALID
    assert "incident ID" in result.reason


def test_request_requires_actor_and_non_empty_justification() -> None:
    with pytest.raises(ValueError, match="principal reference"):
        _request(
            IncidentLifecycleStatus.OPEN,
            IncidentLifecycleStatus.CLOSED,
            actor=None,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="justification"):
        _request(
            IncidentLifecycleStatus.OPEN,
            IncidentLifecycleStatus.CLOSED,
            justification=" ",
        )


def test_transition_requires_utc_timestamp() -> None:
    with pytest.raises(ValueError, match="UTC"):
        _request(
            IncidentLifecycleStatus.OPEN,
            IncidentLifecycleStatus.CLOSED,
            occurred_at=NOW.astimezone(timezone(timedelta(hours=1))),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        _request(
            IncidentLifecycleStatus.OPEN,
            IncidentLifecycleStatus.CLOSED,
            occurred_at=NOW.replace(tzinfo=None),
        )


def test_transition_timestamp_cannot_regress_context_time() -> None:
    context = _context(updated_at=NOW)
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(
            IncidentLifecycleStatus.OPEN,
            IncidentLifecycleStatus.CLOSED,
            occurred_at=NOW - timedelta(seconds=1),
        ),
    )

    assert result.status is IncidentTransitionValidationStatus.INVALID
    assert "precedes incident update" in result.reason


def test_success_returns_immutable_projected_context_without_mutating_input() -> None:
    context = _context(status=IncidentLifecycleStatus.OPEN)
    result = IncidentLifecycleTransitionService().evaluate(
        context,
        _request(IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.INVESTIGATING),
    )

    assert context.lifecycle_status is IncidentLifecycleStatus.OPEN
    assert context.updated_at == NOW - timedelta(minutes=1)
    assert result.resulting_context is not context
    assert result.resulting_context is not None
    assert result.resulting_context.lifecycle_status is IncidentLifecycleStatus.INVESTIGATING


def test_transition_does_not_create_activity_or_cross_domain_effects() -> None:
    result = IncidentLifecycleTransitionService().evaluate(
        _context(),
        _request(IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.CLOSED),
    )

    assert result.resulting_context is not None
    assert not hasattr(result, "activity")
    assert not hasattr(result, "decision")
    assert not hasattr(result, "evidence")
    assert not hasattr(result, "finding")
    assert not hasattr(result, "asset")
    assert not hasattr(result, "response_action")


def test_no_concurrency_status_is_invented_without_context_version() -> None:
    request = _request(IncidentLifecycleStatus.OPEN, IncidentLifecycleStatus.CLOSED)

    assert not hasattr(request, "expected_incident_version")
    assert not hasattr(_context(), "incident_version")


def _context(
    *,
    status: IncidentLifecycleStatus = IncidentLifecycleStatus.OPEN,
    updated_at: datetime = NOW - timedelta(minutes=1),
) -> SecurityIncidentContext:
    return SecurityIncidentContext(
        incident_id="incident-001",
        lifecycle_status=status,
        source="soc",
        source_reference="soc:incident-001",
        title="Controlled incident",
        created_at=NOW - timedelta(hours=1),
        updated_at=updated_at,
    )


def _request(
    expected_status: IncidentLifecycleStatus,
    target_status: IncidentLifecycleStatus,
    *,
    incident_id: str = "incident-001",
    actor: IncidentPrincipalReference | None = ACTOR,
    occurred_at: datetime = NOW,
    justification: str = "Analyst reviewed the incident context.",
) -> IncidentLifecycleTransitionRequest:
    return IncidentLifecycleTransitionRequest(
        incident_id=incident_id,
        expected_status=expected_status,
        target_status=target_status,
        actor=actor,  # type: ignore[arg-type]
        occurred_at=occurred_at,
        justification=justification,
    )

