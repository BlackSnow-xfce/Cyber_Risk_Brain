from datetime import datetime, timedelta, timezone

import pytest

from core.context_supply import ContextObservation, ContextScope, ContextSubject, ContextType, ExposureObservation, ExposureReachability, ObservationProvenance


def observation(now: datetime) -> ContextObservation:
    return ContextObservation.create(organization_id="org-1", context_type=ContextType.EXPOSURE, subject=ContextSubject("asset-1", "finding-1"), scope=ContextScope("https", "/login"), source_id="network-authority", authority_reference="policy:network", provenance=ObservationProvenance("import:network:1", ("route:1",)), observed_at=now, ingested_at=now, valid_until=now + timedelta(hours=1), payload=ExposureObservation(ExposureReachability.AUTHENTICATED_EXTERNAL, True))


def test_observation_has_deterministic_identity_digest_and_freshness() -> None:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = observation(now)
    second = observation(now)
    assert first.observation_id == second.observation_id
    assert first.digest == second.digest
    assert first.is_current(now)
    assert not first.is_current(now + timedelta(hours=1))


def test_observation_rejects_naive_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(datetime(2026, 1, 1))
