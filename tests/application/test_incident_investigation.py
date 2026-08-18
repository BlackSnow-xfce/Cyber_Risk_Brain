from datetime import datetime, timezone

import pytest

from application import (
    FindingAssetContextResolution,
    FindingAssetContextResolutionStatus,
    IncidentInvestigationCandidateStatus,
    IncidentInvestigationFindingInput,
    IncidentInvestigationService,
    IncidentObservation,
    SecurityObservationCorrelationResult,
)
from core.decision.models import (
    Evidence,
    EvidenceKind,
    EvidenceProvenance,
    EvidenceType,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.models import UniversalFinding


def test_resolved_incident_returns_same_asset_finding_as_candidate() -> None:
    result = investigate(finding_inputs=(finding_input(),))

    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.asset_resolution_status is (
        FindingAssetContextResolutionStatus.RESOLVED
    )
    assert result.asset_context == asset_context()
    assert len(result.candidates) == 1
    candidate = result.candidates[0]
    assert candidate.finding.id == "finding-001"
    assert candidate.status is IncidentInvestigationCandidateStatus.CANDIDATE
    assert candidate.correlation_evidence[0].kind is EvidenceKind.DERIVED
    assert candidate.threat_intelligence_references == (
        "threat-intelligence:CVE-2004-2687:nvd:nvd:CVE-2004-2687",
        "threat-intelligence:CVE-2004-2687:cvss:nvd:CVE-2004-2687#cvss",
        "threat-intelligence:CVE-2004-2687:epss:epss:CVE-2004-2687",
        "threat-intelligence:CVE-2004-2687:cisa-kev:cisa-kev:CVE-2004-2687",
    )


def test_multiple_same_asset_findings_are_deterministic_candidates() -> None:
    inputs = (
        finding_input("finding-002", "CVE-2021-44228"),
        finding_input("finding-001", "CVE-2004-2687"),
    )

    result = investigate(finding_inputs=inputs)

    assert tuple(candidate.finding.id for candidate in result.candidates) == (
        "finding-001",
        "finding-002",
    )
    assert all(
        candidate.status is IncidentInvestigationCandidateStatus.CANDIDATE
        for candidate in result.candidates
    )


@pytest.mark.parametrize(
    ("has_identifier", "expected_status", "missing_context"),
    [
        (
            True,
            FindingAssetContextResolutionStatus.NOT_FOUND,
            ("canonical-asset-context",),
        ),
        (
            False,
            FindingAssetContextResolutionStatus.MISSING_IDENTIFIER,
            ("observed-asset-identifier",),
        ),
    ],
)
def test_unresolved_incident_is_controlled_no_data(
    has_identifier: bool,
    expected_status: FindingAssetContextResolutionStatus,
    missing_context: tuple[str, ...],
) -> None:
    result = IncidentInvestigationService().investigate(
        observation(identifier() if has_identifier else None),
        None,
        (finding_input(),),
    )

    assert result.asset_resolution_status is expected_status
    assert result.candidates == ()
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.missing_context == missing_context


def test_resolved_asset_without_matching_findings_is_no_data() -> None:
    other_context = AssetContext(
        observed_identifier=ObservedAssetIdentifier(
            AssetIdentifierType.IP_ADDRESS,
            "192.0.2.25",
        ),
        canonical_asset_id="asset-other",
        criticality=AssetCriticality.HIGH,
        source_reference="product-owner:other",
    )
    item = finding_input(asset=other_context)

    result = investigate(finding_inputs=(item,))

    assert result.candidates == ()
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.missing_context == ("finding-candidates",)


def test_finding_without_correlation_remains_candidate_but_incomplete() -> None:
    item = finding_input(correlation=None)

    result = investigate(finding_inputs=(item,))

    assert len(result.candidates) == 1
    assert result.candidates[0].correlation_evidence == ()
    assert result.candidates[0].completeness.status is CompletenessStatus.NO_DATA
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.missing_context == (
        "correlation-evidence:finding-001:no_data",
    )


def test_unavailable_correlation_status_is_preserved() -> None:
    correlation = correlation_result(
        status=CompletenessStatus.SOURCE_UNAVAILABLE,
        evidence=(),
    )

    result = investigate(
        finding_inputs=(finding_input(correlation=correlation),)
    )

    assert result.completeness.status is CompletenessStatus.SOURCE_UNAVAILABLE
    assert result.candidates[0].completeness.status is (
        CompletenessStatus.SOURCE_UNAVAILABLE
    )
    assert result.missing_context == (
        "correlation-evidence:finding-001:source_unavailable",
    )


def test_no_data_correlation_status_remains_no_data() -> None:
    correlation = correlation_result(
        status=CompletenessStatus.NO_DATA,
        evidence=(),
    )

    result = investigate(
        finding_inputs=(finding_input(correlation=correlation),)
    )

    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.candidates[0].completeness.status is CompletenessStatus.NO_DATA
    assert result.candidates[0].completeness.provenance.source_reference == (
        "correlation-result"
    )
    assert result.missing_context == (
        "correlation-evidence:finding-001:no_data",
    )


def test_insufficient_correlation_provenance_fails_safe() -> None:
    evidence = correlation_evidence(
        input_references=("finding:greenbone:wrong-finding",)
    )

    result = investigate(
        finding_inputs=(
            finding_input(
                correlation=correlation_result(evidence=(evidence,))
            ),
        )
    )

    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.candidates[0].correlation_evidence == ()
    assert result.candidates[0].threat_intelligence_references == ()


def test_missing_observation_time_is_explicitly_incomplete() -> None:
    incident = IncidentObservation(
        incident_id="incident-001",
        source="soc-observation",
        observed_at=None,
        observed_asset_identifier=identifier(),
    )

    result = IncidentInvestigationService().investigate(
        incident,
        asset_context(),
        (finding_input(),),
    )

    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.missing_context == ("incident-observed-timestamp",)


def test_identical_inputs_produce_identical_investigation_context() -> None:
    service = IncidentInvestigationService()
    incident = observation(identifier())
    inputs = (finding_input(),)

    first = service.investigate(incident, asset_context(), inputs)
    second = service.investigate(incident, asset_context(), inputs)

    assert first == second


def test_candidate_contract_contains_no_causality_risk_decision_or_action() -> None:
    candidate = investigate(finding_inputs=(finding_input(),)).candidates[0]

    for forbidden in (
        "confirmed_initial_access",
        "caused_incident",
        "exploited",
        "risk",
        "risk_score",
        "decision",
        "response_action",
        "model",
        "provider",
    ):
        assert not hasattr(candidate, forbidden)


def test_observed_timestamp_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        IncidentObservation(
            incident_id="incident-001",
            source="soc-observation",
            observed_at=datetime(2026, 8, 18, 10, 0),
            observed_asset_identifier=identifier(),
        )


def investigate(
    *,
    finding_inputs: tuple[IncidentInvestigationFindingInput, ...],
):
    return IncidentInvestigationService().investigate(
        observation(identifier()),
        asset_context(),
        finding_inputs,
    )


def observation(
    observed_identifier: ObservedAssetIdentifier | None,
) -> IncidentObservation:
    return IncidentObservation(
        incident_id="incident-lab-001",
        source="controlled-lab-soc-observation",
        observed_at=datetime(2026, 8, 18, 10, 0, tzinfo=timezone.utc),
        observed_asset_identifier=observed_identifier,
    )


def finding_input(
    finding_id: str = "finding-001",
    cve: str = "CVE-2004-2687",
    *,
    asset: AssetContext | None = None,
    correlation: SecurityObservationCorrelationResult | None | object = ...,
) -> IncidentInvestigationFindingInput:
    context = asset or asset_context()
    finding = UniversalFinding(
        id=finding_id,
        source="greenbone",
        title=f"Controlled finding ({cve})",
        vendor_severity="High",
        business_criticality="Unknown",
        asset=context.observed_identifier.value,
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
        cve_identifiers=(cve,),
    )
    resolution = FindingAssetContextResolution(
        finding_id=finding_id,
        finding_source="greenbone",
        finding_title=finding.title,
        status=FindingAssetContextResolutionStatus.RESOLVED,
        observed_identifier=context.observed_identifier,
        asset_context=context,
    )
    selected_correlation = (
        correlation_result(finding_id=finding_id, cve=cve)
        if correlation is ...
        else correlation
    )
    return IncidentInvestigationFindingInput(
        finding=finding,
        asset_resolution=resolution,
        correlation=selected_correlation,
    )


def correlation_result(
    *,
    finding_id: str = "finding-001",
    cve: str = "CVE-2004-2687",
    status: CompletenessStatus = CompletenessStatus.AVAILABLE,
    evidence: tuple[Evidence, ...] | None = None,
) -> SecurityObservationCorrelationResult:
    return SecurityObservationCorrelationResult(
        finding_id=finding_id,
        evidence=(
            (correlation_evidence(finding_id=finding_id, cve=cve),)
            if evidence is None
            else evidence
        ),
        completeness=completeness(status, "correlation-result"),
        asset_context=asset_context(),
    )


def correlation_evidence(
    *,
    finding_id: str = "finding-001",
    cve: str = "CVE-2004-2687",
    input_references: tuple[str, ...] | None = None,
) -> Evidence:
    references = input_references or (
        f"finding:greenbone:{finding_id}",
        (
            "asset-context:asset-lab-metasploitable2-001:"
            "product-owner:metasploitable2-lab-classification"
        ),
        f"threat-intelligence:{cve}:nvd:nvd:{cve}",
        f"threat-intelligence:{cve}:cvss:nvd:{cve}#cvss",
        f"threat-intelligence:{cve}:epss:epss:{cve}",
        f"threat-intelligence:{cve}:cisa-kev:cisa-kev:{cve}",
    )
    return Evidence(
        evidence_type=EvidenceType.CORRELATION,
        key="finding-cve-canonical-asset-correlation",
        value="Candidate correlation only.",
        identifier=f"correlation:{finding_id}:{cve}",
        kind=EvidenceKind.DERIVED,
        provenance=EvidenceProvenance(
            source_type="security_observation_correlation",
            source_reference=f"security-observation-correlation:1.0:{finding_id}:{cve}",
            input_references=references,
        ),
        contract_version="1.0",
    )


def identifier() -> ObservedAssetIdentifier:
    return ObservedAssetIdentifier(
        AssetIdentifierType.IP_ADDRESS,
        "172.18.0.19",
    )


def asset_context() -> AssetContext:
    return AssetContext(
        observed_identifier=identifier(),
        canonical_asset_id="asset-lab-metasploitable2-001",
        criticality=AssetCriticality.LOW,
        source_reference="product-owner:metasploitable2-lab-classification",
    )


def completeness(
    status: CompletenessStatus,
    source_reference: str,
) -> ExplanationCompleteness:
    return ExplanationCompleteness(
        status=status,
        provenance=ExplanationProvenance(
            source_type="security_observation_correlation",
            source_reference=source_reference,
        ),
    )
