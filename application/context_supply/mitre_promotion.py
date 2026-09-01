from datetime import datetime, timezone

from core.context_supply import ContextObservation, ContextType, MitreMapping, ObservationStatus
from .exposure_projection import ContextProjection


class MitrePromoter:
    def promote(self, observations: tuple[ContextObservation, ...], *, organization_id: str, asset_id: str, finding_id: str, binding_key: str, at: datetime | None = None) -> ContextProjection:
        instant = at or datetime.now(timezone.utc)
        matching = tuple(item for item in observations if item.organization_id == organization_id and item.context_type is ContextType.MITRE_MAPPING and item.subject.asset_id == asset_id and item.subject.finding_id == finding_id and isinstance(item.payload, MitreMapping) and item.payload.binding_key in {finding_id, binding_key})
        inactive = {reference for item in matching for reference in (item.revokes_observation_id, item.supersedes_observation_id) if reference}
        current = tuple(item for item in matching if item.observation_id not in inactive and item.revokes_observation_id is None and item.is_current(instant))
        if not current:
            if any(item.revokes_observation_id in {candidate.observation_id for candidate in matching} for item in matching):
                return ContextProjection(ObservationStatus.REVOKED, None, matching, ("non_revoked_mitre_mapping",))
            return ContextProjection(ObservationStatus.STALE if matching else ObservationStatus.UNKNOWN, None, matching, ("current_governed_mitre_mapping",))
        tactics = {item.payload.tactic for item in current if isinstance(item.payload, MitreMapping)}
        if len(tactics) != 1:
            ids = tuple(item.observation_id for item in current)
            return ContextProjection(ObservationStatus.CONFLICTED, None, current, ("unconflicted_mitre_mapping",), ids)
        return ContextProjection(ObservationStatus.CURRENT, tactics.pop(), current)
