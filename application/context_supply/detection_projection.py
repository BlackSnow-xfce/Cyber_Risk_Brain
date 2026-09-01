from datetime import datetime, timezone

from core.context_supply import ContextObservation, ContextType, DetectionCoverageObservation, ObservationStatus
from .exposure_projection import ContextProjection


class DetectionCoverageProjector:
    def project(self, observations: tuple[ContextObservation, ...], *, organization_id: str, asset_id: str, finding_id: str, service: str, path: str, technique_id: str | None = None, at: datetime | None = None) -> ContextProjection:
        instant = at or datetime.now(timezone.utc)
        matching = tuple(item for item in observations if item.organization_id == organization_id and item.context_type is ContextType.DETECTION_COVERAGE and item.subject.asset_id == asset_id and item.subject.finding_id == finding_id and item.scope.service == service and item.scope.path == path and item.scope.technique_id == technique_id)
        inactive = {reference for item in matching for reference in (item.revokes_observation_id, item.supersedes_observation_id) if reference}
        current = tuple(item for item in matching if item.observation_id not in inactive and item.revokes_observation_id is None and item.is_current(instant))
        if not current:
            if any(item.revokes_observation_id in {candidate.observation_id for candidate in matching} for item in matching):
                return ContextProjection(ObservationStatus.REVOKED, None, matching, ("non_revoked_detection_coverage",))
            return ContextProjection(ObservationStatus.STALE if matching else ObservationStatus.UNKNOWN, None, matching, ("current_detection_coverage",))
        values = {item.payload.authoritative_value for item in current if isinstance(item.payload, DetectionCoverageObservation) and item.payload.authoritative_value is not None}
        if len(values) > 1:
            ids = tuple(item.observation_id for item in current)
            return ContextProjection(ObservationStatus.CONFLICTED, None, current, ("unconflicted_detection_coverage",), ids)
        if not values:
            missing = tuple(dict.fromkeys(name for item in current if isinstance(item.payload, DetectionCoverageObservation) for name in item.payload.missing_requirements)) or ("complete_detection_evaluation",)
            return ContextProjection(ObservationStatus.UNKNOWN, None, current, missing)
        return ContextProjection(ObservationStatus.CURRENT, values.pop(), current)
