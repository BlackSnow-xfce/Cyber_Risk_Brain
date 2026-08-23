from datetime import datetime, timezone

from application import IncidentQueueQueryService
from core.incident_response import IncidentLifecycleStatus, SecurityIncidentContext


class Repository:
    def __init__(self, contexts):
        self.contexts = contexts

    def list(self):
        return tuple(self.contexts)


def test_queue_service_projects_canonical_context_fields() -> None:
    context = SecurityIncidentContext(
        incident_id="incident-001",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="controlled-lab",
        source_reference="source:incident-001",
        title="Investigation",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
    )

    items = IncidentQueueQueryService(Repository([context])).list()

    assert len(items) == 1
    assert items[0].incident is context
    assert items[0].participant_count == 0
    assert items[0].finding_count == 0
