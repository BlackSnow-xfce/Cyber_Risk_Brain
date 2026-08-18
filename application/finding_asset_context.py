from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.asset_context import (
    AssetContextQueryService,
    classify_observed_asset_identifier,
)
from application.finding_explanation_use_case import (
    FindingNotFoundError,
    FindingSelectionError,
)
from application.findings_query import FindingsQueryService
from core.enterprise_context import (
    AssetContext,
    ObservedAssetIdentifier,
)


class FindingAssetContextResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    MISSING_IDENTIFIER = "missing_identifier"


@dataclass(frozen=True, slots=True)
class FindingAssetContextResolution:
    finding_id: str
    finding_source: str
    finding_title: str
    status: FindingAssetContextResolutionStatus
    observed_identifier: ObservedAssetIdentifier | None = None
    asset_context: AssetContext | None = None


class FindingAssetContextUseCase:
    """Resolve one finding through the supported canonical identifier types."""

    def __init__(
        self,
        findings: FindingsQueryService,
        asset_contexts: AssetContextQueryService,
    ) -> None:
        self._findings = findings
        self._asset_contexts = asset_contexts

    def resolve(self, finding_id: str) -> FindingAssetContextResolution:
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
        if not finding.asset.strip():
            return FindingAssetContextResolution(
                finding_id=finding.id,
                finding_source=finding.source,
                finding_title=finding.title,
                status=(
                    FindingAssetContextResolutionStatus.MISSING_IDENTIFIER
                ),
            )

        observed_identifier = classify_observed_asset_identifier(
            finding.asset
        )
        if observed_identifier is None:
            return FindingAssetContextResolution(
                finding_id=finding.id,
                finding_source=finding.source,
                finding_title=finding.title,
                status=FindingAssetContextResolutionStatus.NOT_FOUND,
            )
        asset_context = self._asset_contexts.resolve(observed_identifier)

        return FindingAssetContextResolution(
            finding_id=finding.id,
            finding_source=finding.source,
            finding_title=finding.title,
            status=(
                FindingAssetContextResolutionStatus.RESOLVED
                if asset_context is not None
                else FindingAssetContextResolutionStatus.NOT_FOUND
            ),
            observed_identifier=observed_identifier,
            asset_context=asset_context,
        )
