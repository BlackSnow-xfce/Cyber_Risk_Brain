from dataclasses import dataclass
from datetime import datetime, timezone

from core.context_supply import ContextObservation, ContextType, ExposureObservation, ObservationStatus


@dataclass(frozen=True, slots=True)
class ContextProjection:
    status: ObservationStatus
    value: bool | str | None
    observations: tuple[ContextObservation, ...]
    missing_requirements: tuple[str, ...] = ()
    conflict_references: tuple[str, ...] = ()


class ExposureProjector:
    def project(self, observations: tuple[ContextObservation, ...], *, organization_id: str, asset_id: str, finding_id: str, service: str, path: str, at: datetime | None = None) -> ContextProjection:
        instant = at or datetime.now(timezone.utc)
        matching = tuple(item for item in observations if item.organization_id == organization_id and item.context_type is ContextType.EXPOSURE and item.subject.asset_id == asset_id and item.subject.finding_id == finding_id and item.scope.service == service and item.scope.path == path)
        inactive = {reference for item in matching for reference in (item.revokes_observation_id, item.supersedes_observation_id) if reference}
        current = tuple(item for item in matching if item.observation_id not in inactive and item.revokes_observation_id is None and item.is_current(instant))
        if not current:
            if any(item.revokes_observation_id in {candidate.observation_id for candidate in matching} for item in matching):
                return ContextProjection(ObservationStatus.REVOKED, None, matching, ("non_revoked_exposure_evaluation",))
            return ContextProjection(ObservationStatus.STALE if matching else ObservationStatus.UNKNOWN, None, matching, ("current_exposure_evaluation",))
        values = {item.payload.authoritative_value for item in current if isinstance(item.payload, ExposureObservation) and item.payload.authoritative_value is not None}
        if len(values) > 1:
            ids = tuple(item.observation_id for item in current)
            return ContextProjection(ObservationStatus.CONFLICTED, None, current, ("unconflicted_exposure",), ids)
        if not values: return ContextProjection(ObservationStatus.UNKNOWN, None, current, ("authoritative_exposure_evaluation",))
        return ContextProjection(ObservationStatus.CURRENT, values.pop(), current)
