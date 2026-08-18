from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from core.incident_response._validation import required, timezone_aware
from core.incident_response.context import IncidentPrincipalReference


INCIDENT_ACTIVITY_CONTRACT_VERSION = "1.0"


class IncidentActivityType(StrEnum):
    INCIDENT_CREATED = "incident_created"
    LIFECYCLE_CHANGED = "lifecycle_changed"
    ASSIGNMENT_CHANGED = "assignment_changed"
    PARTICIPANT_ADDED = "participant_added"
    PARTICIPANT_REMOVED = "participant_removed"
    ANALYST_NOTE_ADDED = "analyst_note_added"
    ANALYST_NOTE_REVISED = "analyst_note_revised"
    RELATIONSHIP_ADDED = "relationship_added"
    RELATIONSHIP_REMOVED = "relationship_removed"


class IncidentActivityDetailType(StrEnum):
    REASON = "reason"
    PREVIOUS_STATUS = "previous_status"
    NEW_STATUS = "new_status"
    PRINCIPAL_ID = "principal_id"
    NOTE_ID = "note_id"
    NOTE_VERSION_ID = "note_version_id"
    RELATIONSHIP_ID = "relationship_id"


@dataclass(frozen=True, slots=True)
class IncidentActivityDetail:
    detail_type: IncidentActivityDetailType
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.detail_type, IncidentActivityDetailType):
            raise ValueError("Incident activity detail type must be canonical.")
        object.__setattr__(
            self,
            "value",
            required(self.value, "Incident activity detail value"),
        )


@dataclass(frozen=True, slots=True)
class IncidentActivity:
    activity_id: str
    incident_id: str
    activity_type: IncidentActivityType
    actor: IncidentPrincipalReference
    occurred_at: datetime
    sequence: int
    description: str
    details: tuple[IncidentActivityDetail, ...] = ()
    contract_version: str = INCIDENT_ACTIVITY_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "activity_id",
            required(self.activity_id, "Incident activity ID"),
        )
        object.__setattr__(
            self,
            "incident_id",
            required(self.incident_id, "Incident ID"),
        )
        if not isinstance(self.activity_type, IncidentActivityType):
            raise ValueError("Incident activity type must be canonical.")
        if not isinstance(self.actor, IncidentPrincipalReference):
            raise ValueError("Incident activity actor must be a principal reference.")
        timezone_aware(self.occurred_at, "Incident activity timestamp")
        if not isinstance(self.sequence, int) or isinstance(self.sequence, bool):
            raise ValueError("Incident activity sequence must be an integer.")
        if self.sequence < 1:
            raise ValueError("Incident activity sequence must be greater than 0.")
        object.__setattr__(
            self,
            "description",
            required(self.description, "Incident activity description"),
        )
        if any(not isinstance(item, IncidentActivityDetail) for item in self.details):
            raise ValueError("Incident activity details must be canonical.")
        detail_types = tuple(item.detail_type for item in self.details)
        if len(set(detail_types)) != len(detail_types):
            raise ValueError("Incident activity detail types must be unique.")
        object.__setattr__(
            self,
            "contract_version",
            required(self.contract_version, "Incident activity contract version"),
        )

