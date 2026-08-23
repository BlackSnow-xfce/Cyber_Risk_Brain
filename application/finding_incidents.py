from __future__ import annotations

from application.incident_repository import (
    FindingIncidentReference,
    IncidentContextRepository,
)


class FindingIncidentQueryService:
    """Resolve persisted incident relationships for one canonical finding."""

    def __init__(self, repository: IncidentContextRepository) -> None:
        self._repository = repository

    def find_incidents(self, finding_id: str) -> tuple[FindingIncidentReference, ...]:
        normalized_id = finding_id.strip()
        if not normalized_id:
            raise ValueError("Finding ID must not be empty.")
        return self._repository.find_by_finding_id(normalized_id)
