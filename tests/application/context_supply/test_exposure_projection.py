from datetime import datetime, timedelta, timezone

from application.context_supply import ExposureProjector
from core.context_supply import ContextObservation, ContextScope, ContextSubject, ContextType, ExposureObservation, ExposureReachability, ObservationProvenance, ObservationStatus


def item(reachability: ExposureReachability, source: str, now: datetime) -> ContextObservation:
    return ContextObservation.create(organization_id="org", context_type=ContextType.EXPOSURE, subject=ContextSubject("asset", "finding"), scope=ContextScope("https", "/"), source_id=source, authority_reference=f"policy:{source}", provenance=ObservationProvenance(f"import:{source}", (f"route:{source}",)), observed_at=now, ingested_at=now, valid_until=now + timedelta(hours=1), payload=ExposureObservation(reachability, True))


def test_projection_fails_closed_for_conflict_and_stale() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    observations = (item(ExposureReachability.DIRECT_EXTERNAL, "a", now), item(ExposureReachability.NOT_EXTERNALLY_REACHABLE, "b", now))
    conflicted = ExposureProjector().project(observations, organization_id="org", asset_id="asset", finding_id="finding", service="https", path="/", at=now)
    assert conflicted.status is ObservationStatus.CONFLICTED
    assert conflicted.value is None
    stale = ExposureProjector().project((observations[0],), organization_id="org", asset_id="asset", finding_id="finding", service="https", path="/", at=now + timedelta(hours=2))
    assert stale.status is ObservationStatus.STALE
    assert stale.value is None
