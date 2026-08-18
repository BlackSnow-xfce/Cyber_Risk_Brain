from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from core.incident_response import (
    ANALYST_NOTE_CONTRACT_VERSION,
    INCIDENT_ACTIVITY_CONTRACT_VERSION,
    AnalystNote,
    IncidentActivity,
    IncidentActivityDetail,
    IncidentActivityDetailType,
    IncidentActivityType,
    IncidentPrincipalReference,
    IncidentPrincipalType,
)


NOW = datetime(2026, 8, 18, 13, 0, tzinfo=timezone.utc)
ANALYST = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001")
SYSTEM = IncidentPrincipalReference(IncidentPrincipalType.SYSTEM, "predatorai")


def test_valid_incident_activity_with_controlled_details() -> None:
    activity = _activity(
        activity_type=IncidentActivityType.LIFECYCLE_CHANGED,
        details=(
            IncidentActivityDetail(
                IncidentActivityDetailType.PREVIOUS_STATUS,
                "open",
            ),
            IncidentActivityDetail(
                IncidentActivityDetailType.NEW_STATUS,
                "investigating",
            ),
            IncidentActivityDetail(
                IncidentActivityDetailType.REASON,
                "Triage completed",
            ),
        ),
    )

    assert activity.activity_id == "activity-001"
    assert activity.actor == ANALYST
    assert activity.sequence == 1
    assert activity.contract_version == INCIDENT_ACTIVITY_CONTRACT_VERSION


def test_system_principal_can_record_system_originated_incident_activity() -> None:
    activity = _activity(
        actor=SYSTEM,
        activity_type=IncidentActivityType.INCIDENT_CREATED,
    )

    assert activity.actor.principal_type is IncidentPrincipalType.SYSTEM


def test_valid_initial_analyst_note_is_immutable() -> None:
    note = _note()

    assert note.note_id == "note-001"
    assert note.note_version_id == "note-001:version:1"
    assert note.version == 1
    assert note.supersedes_version_id is None
    assert note.contract_version == ANALYST_NOTE_CONTRACT_VERSION
    with pytest.raises(FrozenInstanceError):
        note.content = "Changed"  # type: ignore[misc]


def test_revised_note_references_the_immutable_previous_version() -> None:
    original = _note()
    revision = _note(
        note_version_id="note-001:version:2",
        content="Second analyst observation",
        version=2,
        supersedes_version_id=original.note_version_id,
    )

    assert revision.note_id == original.note_id
    assert revision.note_version_id != original.note_version_id
    assert revision.supersedes_version_id == original.note_version_id
    assert original.content == "Initial analyst observation"


def test_revision_requires_a_superseded_version() -> None:
    with pytest.raises(ValueError, match="must identify the superseded version"):
        _note(note_version_id="note-001:version:2", version=2)


def test_initial_note_cannot_supersede_and_revision_cannot_supersede_itself() -> None:
    with pytest.raises(ValueError, match="must not supersede another version"):
        _note(supersedes_version_id="note-000:version:1")
    with pytest.raises(ValueError, match="must not supersede itself"):
        _note(
            note_version_id="note-001:version:2",
            version=2,
            supersedes_version_id="note-001:version:2",
        )


def test_analyst_note_requires_a_human_user_author() -> None:
    for principal_type in (IncidentPrincipalType.TEAM, IncidentPrincipalType.SYSTEM):
        with pytest.raises(ValueError, match="human user author"):
            _note(
                author=IncidentPrincipalReference(principal_type, "non-human-author")
            )


def test_activity_and_note_timestamps_must_be_timezone_aware() -> None:
    naive = NOW.replace(tzinfo=None)
    with pytest.raises(ValueError, match="timezone-aware"):
        _activity(occurred_at=naive)
    with pytest.raises(ValueError, match="timezone-aware"):
        _note(created_at=naive)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("activity_id", "Incident activity ID"),
        ("incident_id", "Incident ID"),
        ("description", "Incident activity description"),
    ],
)
def test_activity_missing_required_identity_fails_safe(
    field: str,
    message: str,
) -> None:
    values = {
        "activity_id": "activity-001",
        "incident_id": "incident-001",
        "description": "Incident created",
    }
    values[field] = " "

    with pytest.raises(ValueError, match=message):
        _activity(**values)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("note_id", "Analyst note ID"),
        ("note_version_id", "Analyst note version ID"),
        ("incident_id", "Incident ID"),
        ("content", "Analyst note content"),
    ],
)
def test_note_missing_required_identity_or_content_fails_safe(
    field: str,
    message: str,
) -> None:
    values = {
        "note_id": "note-001",
        "note_version_id": "note-001:version:1",
        "incident_id": "incident-001",
        "content": "Initial analyst observation",
    }
    values[field] = " "

    with pytest.raises(ValueError, match=message):
        _note(**values)


def test_activity_sequence_and_detail_types_are_guarded() -> None:
    with pytest.raises(ValueError, match="greater than 0"):
        _activity(sequence=0)
    detail = IncidentActivityDetail(IncidentActivityDetailType.REASON, "reason")
    with pytest.raises(ValueError, match="detail types must be unique"):
        _activity(details=(detail, detail))


def test_activity_and_note_do_not_embed_cross_domain_payloads() -> None:
    activity = _activity()
    note = _note()

    for item in (activity, note):
        assert not hasattr(item, "finding")
        assert not hasattr(item, "asset")
        assert not hasattr(item, "threat_intelligence")
        assert not hasattr(item, "evidence")
        assert not hasattr(item, "decision")
        assert not hasattr(item, "execution_trace")
        assert not hasattr(item, "lifecycle_status")


def test_activity_is_not_evidence_or_execution_trace() -> None:
    activity = _activity()

    assert not hasattr(activity, "evidence_type")
    assert not hasattr(activity, "evidence_kind")
    assert not hasattr(activity, "trace_id")
    assert not hasattr(activity, "execution_status")


def _activity(
    *,
    activity_id: str = "activity-001",
    incident_id: str = "incident-001",
    activity_type: IncidentActivityType = IncidentActivityType.INCIDENT_CREATED,
    actor: IncidentPrincipalReference = ANALYST,
    occurred_at: datetime = NOW,
    sequence: int = 1,
    description: str = "Incident created",
    details: tuple[IncidentActivityDetail, ...] = (),
) -> IncidentActivity:
    return IncidentActivity(
        activity_id=activity_id,
        incident_id=incident_id,
        activity_type=activity_type,
        actor=actor,
        occurred_at=occurred_at,
        sequence=sequence,
        description=description,
        details=details,
    )


def _note(
    *,
    note_id: str = "note-001",
    note_version_id: str = "note-001:version:1",
    incident_id: str = "incident-001",
    author: IncidentPrincipalReference = ANALYST,
    content: str = "Initial analyst observation",
    created_at: datetime = NOW,
    version: int = 1,
    supersedes_version_id: str | None = None,
) -> AnalystNote:
    return AnalystNote(
        note_id=note_id,
        note_version_id=note_version_id,
        incident_id=incident_id,
        author=author,
        content=content,
        created_at=created_at,
        version=version,
        supersedes_version_id=supersedes_version_id,
    )

