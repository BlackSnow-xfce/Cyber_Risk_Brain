from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from application.business_impact_readiness import BusinessContextFact, BusinessImpactReadiness, BusinessImpactReadinessStatus
from application.finding_service_impact_profile import FindingServiceImpactProfileResolution, FindingServiceImpactProfileResolutionStatus
from application.finding_technical_effect import FindingTechnicalEffect, FindingTechnicalEffectProjection, FindingTechnicalEffectStatus
from core.explainability import CompletenessStatus, ExplanationCompleteness, ExplanationProvenance
from core.enterprise_context import BusinessImportance


class BusinessImpactClassificationReadinessStatus(StrEnum):
    READY = "READY"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class BusinessImpactClassificationReadiness:
    finding_id: str
    status: BusinessImpactClassificationReadinessStatus
    reason: str
    business_facts: tuple[BusinessContextFact, ...]
    service_impact_facts: tuple[BusinessContextFact, ...]
    technical_effects: tuple[FindingTechnicalEffect, ...]
    missing_requirements: tuple[str, ...]
    source_references: tuple[str, ...]
    completeness: ExplanationCompleteness

    def __post_init__(self) -> None:
        if type(self.finding_id) is not str or not self.finding_id.strip() or type(self.reason) is not str or not self.reason.strip():
            raise ValueError("Classification readiness identity or reason is invalid.")
        if not isinstance(self.status, BusinessImpactClassificationReadinessStatus):
            raise ValueError("Classification readiness status is invalid.")
        if not isinstance(self.completeness, ExplanationCompleteness):
            raise ValueError("Classification readiness completeness is invalid.")
        for value, label, authority in (
            (self.business_facts, "business facts", BusinessContextFact),
            (self.service_impact_facts, "service-impact facts", BusinessContextFact),
            (self.technical_effects, "technical effects", FindingTechnicalEffect),
        ):
            if not isinstance(value, tuple) or not all(isinstance(item, authority) for item in value):
                raise ValueError(f"Classification readiness {label} are invalid.")
        if not isinstance(self.missing_requirements, tuple) or not all(type(item) is str and item.strip() for item in self.missing_requirements):
            raise ValueError("Classification readiness missing requirements are invalid.")
        if not isinstance(self.source_references, tuple) or not all(type(item) is str and item.strip() for item in self.source_references):
            raise ValueError("Classification readiness source references are invalid.")
        expected = f"business-impact-classification-readiness:{self.status.value.lower()}:{self.finding_id}"
        if self.completeness.provenance.source_type != "business_impact_classification_readiness" or self.completeness.provenance.source_reference != expected:
            raise ValueError("Classification readiness provenance is invalid.")
        referenced = set(self.source_references)
        if any(f.source_reference not in referenced for f in (*self.business_facts, *self.service_impact_facts)) or any(e.source_reference not in referenced for e in self.technical_effects):
            raise ValueError("Classification readiness loses source provenance.")
        if any(effect.finding_id != self.finding_id for effect in self.technical_effects):
            raise ValueError("Classification readiness technical effects identify another finding.")
        for facts in (self.business_facts, self.service_impact_facts):
            names = tuple(fact.name for fact in facts)
            if len(names) != len(set(names)):
                raise ValueError("Classification readiness facts must be unique.")
        if self.status is BusinessImpactClassificationReadinessStatus.READY:
            if self.missing_requirements or self.completeness.status is not CompletenessStatus.AVAILABLE or not self.technical_effects or len(self.service_impact_facts) != 5:
                raise ValueError("Ready classification readiness is inconsistent.")
            business = {fact.name: fact for fact in self.business_facts}
            service = {fact.name: fact for fact in self.service_impact_facts}
            if set(business) != {"canonical_asset_id", "business_service", "environment", "service_criticality"} or set(service) != {"canonical_asset_id", "business_service", "confidentiality_importance", "integrity_importance", "availability_importance"}:
                raise ValueError("Ready classification readiness requires exact authoritative facts.")
            if business["canonical_asset_id"].value != service["canonical_asset_id"].value or business["business_service"].value != service["business_service"].value:
                raise ValueError("Ready classification readiness snapshots are inconsistent.")
            for name in ("confidentiality_importance", "integrity_importance", "availability_importance"):
                try:
                    BusinessImportance(service[name].value)
                except ValueError as error:
                    raise ValueError("Ready classification readiness contains invalid business importance.") from error
        elif self.status is BusinessImpactClassificationReadinessStatus.UNAVAILABLE:
            if not self.missing_requirements or self.completeness.status is CompletenessStatus.AVAILABLE:
                raise ValueError("Unavailable classification readiness is inconsistent.")
        else:
            raise ValueError("Classification readiness status is invalid.")


class BusinessImpactClassificationReadinessService:
    def evaluate(self, business: BusinessImpactReadiness, profile: FindingServiceImpactProfileResolution, technical: FindingTechnicalEffectProjection) -> BusinessImpactClassificationReadiness:
        missing: list[str] = []
        if business.status is not BusinessImpactReadinessStatus.READY:
            missing.extend(business.missing_requirements)
        p = profile.profile
        if profile.status is not FindingServiceImpactProfileResolutionStatus.RESOLVED or p is None:
            missing.append("service_impact_profile")
        if technical.status is not FindingTechnicalEffectStatus.AVAILABLE:
            missing.extend(technical.missing_requirements)
        service_facts = () if p is None else (
            BusinessContextFact("canonical_asset_id", p.canonical_asset_id, p.source_reference),
            BusinessContextFact("business_service", p.business_service, p.source_reference),
            BusinessContextFact("confidentiality_importance", p.confidentiality_importance.value, p.source_reference),
            BusinessContextFact("integrity_importance", p.integrity_importance.value, p.source_reference),
            BusinessContextFact("availability_importance", p.availability_importance.value, p.source_reference),
        )
        sources = tuple(dict.fromkeys((*business.source_references, *(f.source_reference for f in service_facts), *(e.source_reference for e in technical.effects))))
        status = BusinessImpactClassificationReadinessStatus.UNAVAILABLE if missing else BusinessImpactClassificationReadinessStatus.READY
        completeness_status = CompletenessStatus.NO_DATA if missing else CompletenessStatus.AVAILABLE
        return BusinessImpactClassificationReadiness(
            finding_id=business.finding_id, status=status,
            reason=("Business-impact classification prerequisites are unavailable." if missing else "All authoritative classification prerequisites are available."),
            business_facts=business.facts, service_impact_facts=service_facts,
            technical_effects=technical.effects, missing_requirements=tuple(dict.fromkeys(missing)), source_references=sources,
            completeness=ExplanationCompleteness(completeness_status, ExplanationProvenance("business_impact_classification_readiness", f"business-impact-classification-readiness:{status.value.lower()}:{business.finding_id}")),
        )
