from datetime import datetime, timedelta, timezone

import pytest

from application.context_supply import FileContextObservationRepository
from core.context_supply import ContextObservation, ContextScope, ContextSubject, ContextType, ExposureObservation, ExposureReachability, ObservationProvenance


def make_observation() -> ContextObservation:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return ContextObservation.create(organization_id="org-1", context_type=ContextType.EXPOSURE, subject=ContextSubject("asset-1", "finding-1"), scope=ContextScope("https", "/"), source_id="network-authority", authority_reference="policy:1", provenance=ObservationProvenance("import:1", ("route:1",)), observed_at=now, ingested_at=now, valid_until=now + timedelta(hours=1), payload=ExposureObservation(ExposureReachability.DIRECT_EXTERNAL, True))


def test_repository_is_immutable_idempotent_and_verifies_readback(tmp_path) -> None:
    repository = FileContextObservationRepository(tmp_path)
    value = make_observation()
    assert repository.add(value) == value
    assert repository.add(value) == value
    stored = tmp_path / f"{value.observation_id}.json"
    stored.write_text(stored.read_text().replace(value.digest, "0" * 64), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid"):
        repository.get(value.observation_id)
