from __future__ import annotations

from application.asset_context import (
    AssetContextQueryService,
    classify_observed_asset_identifier,
)
from application.finding_explanation import (
    FindingExplanationInputBuilder,
    FindingExplanationResult,
    FindingExplanationService,
)
from application.findings_query import FindingsQueryService
from application.risk_readiness import (
    RiskAssessmentInput,
    RiskReadinessService,
)


class FindingNotFoundError(LookupError):
    """Raised when the configured source has no matching finding."""


class FindingSelectionError(ValueError):
    """Raised when a finding ID is not unique in the configured source."""


class FindingExplanationUseCase:
    """Run the existing explanation capability for one live finding."""

    def __init__(
        self,
        findings: FindingsQueryService,
        asset_contexts: AssetContextQueryService,
        risk_readiness: RiskReadinessService,
        explanations: FindingExplanationService,
    ) -> None:
        self._findings = findings
        self._asset_contexts = asset_contexts
        self._risk_readiness = risk_readiness
        self._explanations = explanations

    def explain(self, finding_id: str) -> FindingExplanationResult:
        matches = [
            finding
            for finding in self._findings.get_findings()
            if finding.id == finding_id
        ]
        if not matches:
            raise FindingNotFoundError(finding_id)
        if len(matches) > 1:
            raise FindingSelectionError(
                "Configured finding source contains a duplicate finding ID."
            )

        finding = matches[0]
        observed_identifier = classify_observed_asset_identifier(
            finding.asset
        )
        asset_context = (
            self._asset_contexts.resolve(observed_identifier)
            if observed_identifier is not None
            else None
        )
        risk_input = RiskAssessmentInput.from_universal_finding(
            finding
        ).with_asset_context(asset_context)
        risk_result = self._risk_readiness.assess(risk_input)
        explanation_input = FindingExplanationInputBuilder.build(
            finding,
            asset_context,
            risk_input,
            risk_result,
        )
        return self._explanations.explain(explanation_input)
