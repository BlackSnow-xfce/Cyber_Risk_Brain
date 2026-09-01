from dataclasses import dataclass, replace
from datetime import datetime

from application.risk_readiness import RiskAssessmentInput, RiskInputValue
from core.context_supply import ObservationStatus
from .detection_projection import DetectionCoverageProjector
from .exposure_projection import ContextProjection
from .exposure_projection import ExposureProjector
from .mitre_promotion import MitrePromoter
from .repository import ContextObservationRepository


@dataclass(frozen=True, slots=True)
class RiskInputPromotionResult:
    risk_input: RiskAssessmentInput
    exposure: ContextProjection
    detection: ContextProjection
    mitre: ContextProjection


class RiskInputPromoter:
    def promote(self, risk_input: RiskAssessmentInput, *, exposure: ContextProjection, detection: ContextProjection, threat_intelligence_match: bool | None, mitre: ContextProjection) -> RiskAssessmentInput:
        return replace(risk_input,
            exposure=RiskInputValue.authoritative(exposure.value, self._source(exposure)) if isinstance(exposure.value, bool) else risk_input.exposure,
            detection_available=RiskInputValue.authoritative(detection.value, self._source(detection)) if isinstance(detection.value, bool) else risk_input.detection_available,
            threat_intelligence_match=RiskInputValue.authoritative(True, "correlation-derived-evidence") if threat_intelligence_match is True else risk_input.threat_intelligence_match,
            mitre_tactic=RiskInputValue.authoritative(mitre.value, self._source(mitre)) if isinstance(mitre.value, str) else risk_input.mitre_tactic,
        )

    @staticmethod
    def _source(projection: ContextProjection) -> str:
        return ",".join(item.observation_id for item in projection.observations)


class ContextSupplyRiskInputService:
    def __init__(self, repository: ContextObservationRepository, organization_id: str) -> None:
        if not organization_id.strip():
            raise ValueError("Configured organization is required.")
        self._repository = repository
        self._organization_id = organization_id

    def promote(self, risk_input: RiskAssessmentInput, *, threat_intelligence_match: bool | None, at: datetime | None = None) -> RiskInputPromotionResult:
        observations = self._repository.list(organization_id=self._organization_id, asset_id=risk_input.asset, finding_id=risk_input.finding_id)
        exposure_scope = self._single_scope(observations, "EXPOSURE")
        detection_scope = self._single_scope(observations, "DETECTION_COVERAGE")
        mitre_scope = self._single_scope(observations, "MITRE_MAPPING")
        exposure = ExposureProjector().project(observations, organization_id=self._organization_id, asset_id=risk_input.asset, finding_id=risk_input.finding_id, service=exposure_scope[0], path=exposure_scope[1], at=at) if exposure_scope else ContextProjection(ObservationStatus.UNKNOWN, None, (), ("authoritative_exposure_evaluation",))
        detection = DetectionCoverageProjector().project(observations, organization_id=self._organization_id, asset_id=risk_input.asset, finding_id=risk_input.finding_id, service=detection_scope[0], path=detection_scope[1], technique_id=detection_scope[2], at=at) if detection_scope else ContextProjection(ObservationStatus.UNKNOWN, None, (), ("authoritative_detection_coverage",))
        mitre = MitrePromoter().promote(observations, organization_id=self._organization_id, asset_id=risk_input.asset, finding_id=risk_input.finding_id, binding_key=risk_input.finding_id, at=at) if mitre_scope else ContextProjection(ObservationStatus.UNKNOWN, None, (), ("current_governed_mitre_mapping",))
        promoted = RiskInputPromoter().promote(risk_input, exposure=exposure, detection=detection, threat_intelligence_match=threat_intelligence_match, mitre=mitre)
        return RiskInputPromotionResult(promoted, exposure, detection, mitre)

    @staticmethod
    def _single_scope(observations, context_type: str):
        scopes = {(item.scope.service, item.scope.path, item.scope.technique_id) for item in observations if item.context_type.value == context_type}
        return next(iter(scopes)) if len(scopes) == 1 else None
