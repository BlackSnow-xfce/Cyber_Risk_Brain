from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.incident_response._validation import required, timezone_aware
from core.incident_response.context import (
    IncidentPrincipalReference,
    IncidentPrincipalType,
)


ANALYST_NOTE_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class AnalystNote:
    note_id: str
    note_version_id: str
    incident_id: str
    author: IncidentPrincipalReference
    content: str
    created_at: datetime
    version: int
    supersedes_version_id: str | None = None
    contract_version: str = ANALYST_NOTE_CONTRACT_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "note_id", required(self.note_id, "Analyst note ID"))
        object.__setattr__(
            self,
            "note_version_id",
            required(self.note_version_id, "Analyst note version ID"),
        )
        object.__setattr__(
            self,
            "incident_id",
            required(self.incident_id, "Incident ID"),
        )
        if not isinstance(self.author, IncidentPrincipalReference):
            raise ValueError("Analyst note author must be a principal reference.")
        if self.author.principal_type is not IncidentPrincipalType.USER:
            raise ValueError("Analyst notes require a human user author.")
        object.__setattr__(self, "content", required(self.content, "Analyst note content"))
        timezone_aware(self.created_at, "Analyst note created timestamp")
        if not isinstance(self.version, int) or isinstance(self.version, bool):
            raise ValueError("Analyst note version must be an integer.")
        if self.version < 1:
            raise ValueError("Analyst note version must be greater than 0.")
        if self.version == 1 and self.supersedes_version_id is not None:
            raise ValueError("Initial analyst note version must not supersede another version.")
        if self.version > 1 and self.supersedes_version_id is None:
            raise ValueError("Revised analyst note versions must identify the superseded version.")
        if self.supersedes_version_id is not None:
            supersedes = required(
                self.supersedes_version_id,
                "Superseded analyst note version ID",
            )
            if supersedes == self.note_version_id:
                raise ValueError("Analyst note version must not supersede itself.")
            object.__setattr__(self, "supersedes_version_id", supersedes)
        object.__setattr__(
            self,
            "contract_version",
            required(self.contract_version, "Analyst note contract version"),
        )

