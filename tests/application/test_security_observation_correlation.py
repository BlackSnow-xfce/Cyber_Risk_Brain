from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timezone

import pytest

from application import (
    FindingAssetContextResolution,
    FindingAssetContextResolutionStatus,
    FindingThreatIntelligenceEnrichment,
    SecurityObservationCorrelationApplicationService,
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
from core.security_observation import SecurityObservationCorrelationService
from core.threat_intelligence import (
    CisaKevInformation,
    CveIdentifier,
    CvssInformation,
    EpssInformation,
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)


class StubFindingThreatIntelligence:
    def __init__(self, enrichment: FindingThreatIntelligenceEnrichment) -> None:
        self.enrichment = enrichment
        self.calls = 0

    def enrich(self, finding_id: str) -> FindingThreatIntelligenceEnrichment:
        self.calls += 1
        assert finding_id == self.enrichment.finding_id
        return self.enrichment


class StubFindingAssetContext:
    def __init__(self, resolution: FindingAssetContextResolution) -> None:
        self.resolution = resolution
        self.calls = 0

    def resolve(self, finding_id: str) -> FindingAssetContextResolution:
        self.calls += 1
        assert finding_id == self.resolution.finding_id
        return self.resolution


def test_complete_inputs_create_deterministic_derived_evidence() -> None:
    service = application_service()

    first = service.correlate("finding-001")
    second = service.correlate("finding-001")

    assert first == second
    assert first.completeness.status is CompletenessStatus.AVAILABLE
    assert len(first.evidence) == 1
    evidence = first.evidence[0]
    assert evidence.identifier == "correlation:finding-001:CVE-2004-2687"
    assert evidence.evidence_type is EvidenceType.CORRELATION
    assert evidence.kind is EvidenceKind.DERIVED
    assert evidence.contract_version == "1.0"
    assert "risk" not in evidence.key
    assert "priority" not in evidence.key
    assert "decision" not in evidence.key


def test_caller_owned_snapshot_is_correlated_without_source_rereads() -> None:
    resolution = asset_resolution()
    observed_at = datetime(2026, 8, 31, 12, 0, tzinfo=timezone.utc)
    snapshot = enrichment(
        replace(
            intelligence(),
            nvd=replace(
                intelligence().nvd,
                observed_at=observed_at,
            ),
        )
    )
    ti = StubFindingThreatIntelligence(enrichment(intelligence()))
    assets = StubFindingAssetContext(resolution)
    service = SecurityObservationCorrelationApplicationService(
        ti,
        assets,
        SecurityObservationCorrelationService(),
    )

    result = service.correlate_snapshot("finding-001", resolution, snapshot)

    assert assets.calls == 0
    assert ti.calls == 0
    assert result.asset_context is resolution.asset_context
    assert result.threat_intelligence is snapshot.relationships
    vulnerability = result.threat_intelligence[0].vulnerability
    assert vulnerability is not None
    assert vulnerability.nvd.observed_at == observed_at


def test_unresolved_caller_snapshot_preserves_ti_without_deriving_evidence() -> None:
    resolution = asset_resolution(
        status=FindingAssetContextResolutionStatus.NOT_FOUND
    )
    snapshot = enrichment(intelligence())
    service = application_service()

    result = service.correlate_snapshot("finding-001", resolution, snapshot)

    assert result.evidence == ()
    assert result.asset_context is None
    assert result.threat_intelligence is snapshot.relationships
    assert result.completeness.status is CompletenessStatus.NO_DATA


def test_derived_evidence_retains_all_source_input_references() -> None:
    evidence = application_service().correlate("finding-001").evidence[0]

    assert evidence.provenance is not None
    assert evidence.provenance.source_type == (
        "security_observation_correlation"
    )
    assert evidence.provenance.input_references == (
        "finding:greenbone:finding-001",
        (
            "asset-context:asset-lab-metasploitable2-001:"
            "product-owner:metasploitable2-lab-classification"
        ),
        "threat-intelligence:CVE-2004-2687:nvd:nvd:CVE-2004-2687",
        "threat-intelligence:CVE-2004-2687:cvss:nvd:CVE-2004-2687#cvss",
        "threat-intelligence:CVE-2004-2687:epss:epss:CVE-2004-2687",
        (
            "threat-intelligence:CVE-2004-2687:cisa-kev:"
            "cisa-kev:CVE-2004-2687"
        ),
    )


def test_canonical_derived_evidence_is_immutable() -> None:
    evidence = application_service().correlate("finding-001").evidence[0]

    with pytest.raises(FrozenInstanceError):
        evidence.value = "changed"


def test_source_and_derived_evidence_kinds_remain_distinct() -> None:
    source = Evidence(
        evidence_type=EvidenceType.FINDING,
        key="finding-reference",
        value="finding-001",
        identifier="source:finding-001",
        kind=EvidenceKind.SOURCE,
        provenance=EvidenceProvenance(
            source_type="greenbone",
            source_reference="finding:greenbone:finding-001",
        ),
        contract_version="1.0",
    )
    derived = application_service().correlate("finding-001").evidence[0]

    assert source.kind is EvidenceKind.SOURCE
    assert source.provenance is not None
    assert source.provenance.input_references == ()
    assert derived.kind is EvidenceKind.DERIVED
    assert derived.provenance is not None
    assert derived.provenance.input_references


def test_unavailable_required_ti_fails_safe_without_derived_evidence() -> None:
    result = application_service(
        vulnerability=intelligence(
            epss_status=CompletenessStatus.SOURCE_UNAVAILABLE
        )
    ).correlate("finding-001")

    assert result.evidence == ()
    assert result.completeness.status is CompletenessStatus.SOURCE_UNAVAILABLE
    assert result.asset_context is not None
    assert len(result.threat_intelligence) == 1
    vulnerability = result.threat_intelligence[0].vulnerability
    assert vulnerability is not None
    assert vulnerability.epss.value is None
    assert vulnerability.epss.completeness.status is (
        CompletenessStatus.SOURCE_UNAVAILABLE
    )
    assert result.completeness.provenance.source_reference == (
        "required-threat-intelligence-incomplete:epss=source_unavailable"
    )


def test_missing_cvss_preserves_no_data_without_derived_evidence() -> None:
    result = application_service(
        vulnerability=intelligence(cvss_status=CompletenessStatus.NO_DATA)
    ).correlate("finding-001")

    assert result.evidence == ()
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.completeness.provenance.source_reference == (
        "required-threat-intelligence-incomplete:cvss=no_data"
    )
    vulnerability = result.threat_intelligence[0].vulnerability
    assert vulnerability is not None
    assert vulnerability.nvd.completeness.status is CompletenessStatus.AVAILABLE
    assert vulnerability.cvss.value is None
    assert vulnerability.cvss.completeness.status is CompletenessStatus.NO_DATA


def test_mixed_incomplete_facts_use_deterministic_canonical_precedence() -> None:
    vulnerability = intelligence(
        cvss_status=CompletenessStatus.NO_DATA,
        epss_status=CompletenessStatus.SOURCE_UNAVAILABLE,
    )

    first = application_service(vulnerability=vulnerability).correlate(
        "finding-001"
    )
    second = application_service(vulnerability=vulnerability).correlate(
        "finding-001"
    )

    assert first == second
    assert first.evidence == ()
    assert first.completeness.status is CompletenessStatus.SOURCE_UNAVAILABLE
    assert first.completeness.provenance.source_reference == (
        "required-threat-intelligence-incomplete:"
        "cvss=no_data,epss=source_unavailable"
    )


@pytest.mark.parametrize(
    "status",
    [
        FindingAssetContextResolutionStatus.NOT_FOUND,
        FindingAssetContextResolutionStatus.MISSING_IDENTIFIER,
    ],
)
def test_unresolved_asset_fails_safe_and_skips_ti(
    status: FindingAssetContextResolutionStatus,
) -> None:
    ti = StubFindingThreatIntelligence(enrichment(intelligence()))
    result = SecurityObservationCorrelationApplicationService(
        ti,
        StubFindingAssetContext(asset_resolution(status=status)),
        SecurityObservationCorrelationService(),
    ).correlate("finding-001")

    assert result.evidence == ()
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.asset_context is None
    assert result.threat_intelligence == ()
    assert ti.calls == 0


def test_no_cve_is_not_applicable_without_correlation_evidence() -> None:
    no_cve = FindingThreatIntelligenceEnrichment(
        finding_id="finding-001",
        finding_source="greenbone",
        finding_title="Controlled finding",
        relationships=(
            FindingThreatIntelligence(
                finding_id="finding-001",
                applicability=FindingIntelligenceApplicability.NOT_APPLICABLE,
            ),
        ),
    )
    result = application_service(enrichment_value=no_cve).correlate("finding-001")

    assert result.evidence == ()
    assert result.completeness.status is CompletenessStatus.NOT_APPLICABLE


def test_result_contains_no_risk_decision_or_llm_contract() -> None:
    result = application_service().correlate("finding-001")

    for forbidden in (
        "risk",
        "risk_score",
        "priority",
        "decision",
        "recommendation",
        "model",
        "provider",
        "prompt",
    ):
        assert not hasattr(result, forbidden)
        assert not hasattr(result.evidence[0], forbidden)


def application_service(
    *,
    vulnerability: VulnerabilityThreatIntelligence | None = None,
    enrichment_value: FindingThreatIntelligenceEnrichment | None = None,
) -> SecurityObservationCorrelationApplicationService:
    return SecurityObservationCorrelationApplicationService(
        StubFindingThreatIntelligence(
            enrichment_value or enrichment(vulnerability or intelligence())
        ),
        StubFindingAssetContext(asset_resolution()),
        SecurityObservationCorrelationService(),
    )


def asset_resolution(
    *,
    status: FindingAssetContextResolutionStatus = (
        FindingAssetContextResolutionStatus.RESOLVED
    ),
) -> FindingAssetContextResolution:
    resolved = status is FindingAssetContextResolutionStatus.RESOLVED
    return FindingAssetContextResolution(
        finding_id="finding-001",
        finding_source="greenbone",
        finding_title="Controlled finding",
        status=status,
        observed_identifier=identifier() if resolved else None,
        asset_context=asset_context() if resolved else None,
    )


def identifier() -> ObservedAssetIdentifier:
    return ObservedAssetIdentifier(
        identifier_type=AssetIdentifierType.IP_ADDRESS,
        value="172.18.0.19",
    )


def asset_context() -> AssetContext:
    return AssetContext(
        observed_identifier=identifier(),
        canonical_asset_id="asset-lab-metasploitable2-001",
        criticality=AssetCriticality.LOW,
        source_reference=(
            "product-owner:metasploitable2-lab-classification"
        ),
    )


def enrichment(
    vulnerability: VulnerabilityThreatIntelligence,
) -> FindingThreatIntelligenceEnrichment:
    return FindingThreatIntelligenceEnrichment(
        finding_id="finding-001",
        finding_source="greenbone",
        finding_title="Controlled finding",
        relationships=(
            FindingThreatIntelligence(
                finding_id="finding-001",
                applicability=FindingIntelligenceApplicability.APPLICABLE,
                vulnerability=vulnerability,
            ),
        ),
    )


def intelligence(
    *,
    cvss_status: CompletenessStatus = CompletenessStatus.AVAILABLE,
    epss_status: CompletenessStatus = CompletenessStatus.AVAILABLE,
) -> VulnerabilityThreatIntelligence:
    cve = CveIdentifier("CVE-2004-2687")
    return VulnerabilityThreatIntelligence(
        cve_identifier=cve,
        nvd=fact(
            NvdIntelligence(summary="Controlled NVD description."),
            "nvd",
            "nvd:CVE-2004-2687",
        ),
        cvss=fact(
            (
                CvssInformation(
                    version="2.0",
                    base_score=9.3,
                    severity="HIGH",
                    vector="AV:N/AC:M/Au:N/C:C/I:C/A:C",
                )
                if cvss_status is CompletenessStatus.AVAILABLE
                else None
            ),
            "nvd",
            "nvd:CVE-2004-2687#cvss",
            status=cvss_status,
        ),
        epss=fact(
            EpssInformation(probability=0.88195, percentile=0.99755)
            if epss_status is CompletenessStatus.AVAILABLE
            else None,
            "epss",
            "epss:CVE-2004-2687",
            status=epss_status,
        ),
        cisa_kev=fact(
            CisaKevInformation(known_exploited=False),
            "cisa_kev",
            "cisa-kev:CVE-2004-2687",
        ),
        exploitation_evidence=fact(
            None,
            "cisa_kev",
            "cisa-kev:CVE-2004-2687#exploitation-evidence",
            status=CompletenessStatus.NOT_EVALUATED,
        ),
    )


def fact(
    value: object | None,
    source_type: str,
    source_reference: str,
    *,
    status: CompletenessStatus = CompletenessStatus.AVAILABLE,
) -> IntelligenceFact[object]:
    return IntelligenceFact(
        value=value,
        completeness=ExplanationCompleteness(
            status=status,
            provenance=ExplanationProvenance(
                source_type=source_type,
                source_reference=source_reference,
            ),
        ),
    )
