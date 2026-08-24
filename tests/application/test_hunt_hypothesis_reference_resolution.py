from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from application import (
    AssetContextConfigurationError,
    AssetContextDataError,
    FindingsConfigurationError,
    HuntHypothesisNotFoundError,
    HuntHypothesisQueryService,
    HuntHypothesisReferenceIntegrityError,
    HuntHypothesisReferenceResolutionService,
    HuntHypothesisReferenceResolutionStatus,
    ThreatIntelligenceConfigurationError,
    ThreatIntelligenceNotFoundError,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.models import UniversalFinding
from core.threat_hunting import (
    HuntHypothesis,
    HuntHypothesisReference,
    HuntHypothesisReferenceType,
    HuntHypothesisStatus,
)


class HypothesisRepository:
    def __init__(self, hypotheses: tuple[HuntHypothesis, ...]) -> None:
        self.hypotheses = hypotheses

    def list(self) -> tuple[HuntHypothesis, ...]:
        return self.hypotheses


class FindingsSource:
    def __init__(self, findings=(), error: Exception | None = None) -> None:
        self.findings = list(findings)
        self.error = error

    def get_findings(self):
        if self.error:
            raise self.error
        return self.findings


class AssetSource:
    def __init__(self, asset=None, error: Exception | None = None) -> None:
        self.asset = asset
        self.error = error

    def resolve_canonical_asset(self, canonical_asset_id: str):
        if self.error:
            raise self.error
        return self.asset


class CveSource:
    def __init__(self, intelligence=None, error: Exception | None = None) -> None:
        self.intelligence = intelligence
        self.error = error

    def get_by_cve(self, cve: str):
        if self.error:
            raise self.error
        return self.intelligence


def test_finding_resolved() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.FINDING, "finding-001"),
        findings=FindingsSource([_finding()]),
    )

    assert resolution.resolution_status is _status("resolved")
    assert resolution.authoritative_source == "findings"
    assert resolution.resolved_identity == "finding-001"
    assert resolution.source_reference == "greenbone"


def test_finding_not_found() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.FINDING, "missing"),
        findings=FindingsSource([_finding()]),
    )

    assert resolution.resolution_status is _status("not_found")


def test_finding_source_unavailable() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.FINDING, "finding-001"),
        findings=FindingsSource(error=FindingsConfigurationError("missing")),
    )

    assert resolution.resolution_status is _status("source_unavailable")


def test_asset_resolved() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.ASSET, "asset-001"),
        assets=AssetSource(_asset()),
    )

    assert resolution.resolution_status is _status("resolved")
    assert resolution.authoritative_source == "asset_context"
    assert resolution.source_reference == "asset-source:001"


def test_asset_not_found() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.ASSET, "asset-001"),
        assets=AssetSource(),
    )

    assert resolution.resolution_status is _status("not_found")


def test_asset_source_unavailable() -> None:
    resolution = _resolve(
        _target(HuntHypothesisReferenceType.ASSET, "asset-001"),
        assets=AssetSource(error=AssetContextConfigurationError("missing")),
    )

    assert resolution.resolution_status is _status("source_unavailable")


def test_cve_resolved() -> None:
    resolution = _resolve(
        _threat(HuntHypothesisReferenceType.CVE, "CVE-2026-1234"),
        cves=CveSource(_intelligence()),
    )

    assert resolution.resolution_status is _status("resolved")
    assert resolution.authoritative_source == "threat_intelligence"
    assert resolution.source_reference == "contract:1.0"


def test_cve_not_found() -> None:
    resolution = _resolve(
        _threat(HuntHypothesisReferenceType.CVE, "CVE-2026-1234"),
        cves=CveSource(error=ThreatIntelligenceNotFoundError("missing")),
    )

    assert resolution.resolution_status is _status("not_found")


def test_cve_source_unavailable() -> None:
    resolution = _resolve(
        _threat(HuntHypothesisReferenceType.CVE, "CVE-2026-1234"),
        cves=CveSource(error=ThreatIntelligenceConfigurationError("missing")),
    )

    assert resolution.resolution_status is _status("source_unavailable")


@pytest.mark.parametrize(
    ("reference_type", "is_target"),
    [
        (HuntHypothesisReferenceType.SERVICE, True),
        (HuntHypothesisReferenceType.THREAT_INTELLIGENCE, False),
        (HuntHypothesisReferenceType.TECHNIQUE, False),
        (HuntHypothesisReferenceType.TACTIC, False),
    ],
)
def test_unapproved_reference_types_are_explicitly_unsupported(
    reference_type: HuntHypothesisReferenceType, is_target: bool
) -> None:
    reference = (
        _target(reference_type, "reference-001")
        if is_target
        else _threat(reference_type, "reference-001")
    )

    resolution = _resolve(reference)

    assert resolution.resolution_status is _status("unsupported")
    assert resolution.authoritative_source is None


def test_mixed_references_preserve_per_reference_statuses() -> None:
    hypothesis = _hypothesis(
        targets=(
            _target(HuntHypothesisReferenceType.FINDING, "finding-001"),
            _target(HuntHypothesisReferenceType.ASSET, "missing-asset"),
            _target(HuntHypothesisReferenceType.SERVICE, "tcp:443"),
        ),
        threats=(
            _threat(HuntHypothesisReferenceType.CVE, "CVE-2026-1234"),
        ),
    )
    service = _service(
        hypothesis,
        findings=FindingsSource([_finding()]),
        assets=AssetSource(),
        cves=CveSource(error=ThreatIntelligenceConfigurationError("missing")),
    )

    result = service.resolve(hypothesis.hypothesis_id)

    assert [item.resolution_status.value for item in result.references] == [
        "resolved",
        "not_found",
        "unsupported",
        "source_unavailable",
    ]


def test_duplicate_finding_identity_fails_the_whole_resolution() -> None:
    hypothesis = _hypothesis(
        targets=(_target(HuntHypothesisReferenceType.FINDING, "finding-001"),)
    )
    service = _service(
        hypothesis,
        findings=FindingsSource([_finding(), _finding()]),
    )

    with pytest.raises(HuntHypothesisReferenceIntegrityError, match="duplicate"):
        service.resolve(hypothesis.hypothesis_id)


def test_asset_ambiguity_fails_the_whole_resolution() -> None:
    hypothesis = _hypothesis(
        targets=(_target(HuntHypothesisReferenceType.ASSET, "asset-001"),)
    )
    service = _service(
        hypothesis,
        assets=AssetSource(error=AssetContextDataError("ambiguous")),
    )

    with pytest.raises(HuntHypothesisReferenceIntegrityError):
        service.resolve(hypothesis.hypothesis_id)


def test_hypothesis_not_found() -> None:
    service = HuntHypothesisReferenceResolutionService(
        HuntHypothesisQueryService(HypothesisRepository(())),
        FindingsSource(),
        AssetSource(),
        CveSource(),
    )

    with pytest.raises(HuntHypothesisNotFoundError):
        service.resolve("missing")


def _resolve(
    reference: HuntHypothesisReference,
    *,
    findings: FindingsSource | None = None,
    assets: AssetSource | None = None,
    cves: CveSource | None = None,
):
    is_target = reference.reference_type in {
        HuntHypothesisReferenceType.ASSET,
        HuntHypothesisReferenceType.SERVICE,
        HuntHypothesisReferenceType.FINDING,
    }
    hypothesis = _hypothesis(
        targets=(reference,) if is_target else (),
        threats=() if is_target else (reference,),
    )
    return _service(
        hypothesis, findings=findings, assets=assets, cves=cves
    ).resolve(hypothesis.hypothesis_id).references[0]


def _service(
    hypothesis: HuntHypothesis,
    *,
    findings: FindingsSource | None = None,
    assets: AssetSource | None = None,
    cves: CveSource | None = None,
) -> HuntHypothesisReferenceResolutionService:
    return HuntHypothesisReferenceResolutionService(
        HuntHypothesisQueryService(HypothesisRepository((hypothesis,))),
        findings or FindingsSource(),
        assets or AssetSource(),
        cves or CveSource(),
    )


def _hypothesis(
    *,
    targets: tuple[HuntHypothesisReference, ...] = (),
    threats: tuple[HuntHypothesisReference, ...] = (),
) -> HuntHypothesis:
    return HuntHypothesis(
        hypothesis_id="hypothesis-001",
        title="Controlled hypothesis",
        statement="A controlled condition may warrant investigation.",
        status=HuntHypothesisStatus.DRAFT,
        created_at=datetime(2026, 8, 25, tzinfo=timezone.utc),
        created_by="threat-hunter-001",
        target_references=targets,
        threat_references=threats,
        rationale="Controlled test rationale.",
    )


def _target(
    reference_type: HuntHypothesisReferenceType, reference_id: str
) -> HuntHypothesisReference:
    return HuntHypothesisReference(reference_type, reference_id)


def _threat(
    reference_type: HuntHypothesisReferenceType, reference_id: str
) -> HuntHypothesisReference:
    return HuntHypothesisReference(reference_type, reference_id)


def _finding() -> UniversalFinding:
    return UniversalFinding(
        id="finding-001",
        source="greenbone",
        title="Controlled Finding",
        vendor_severity="High",
        business_criticality="UNKNOWN",
        asset="192.0.2.10",
        exposed=False,
        detection_available=False,
        threat_intel_match=False,
        mitre_tactic=None,
        owner=None,
        remediation=None,
    )


def _asset() -> AssetContext:
    return AssetContext(
        observed_identifier=ObservedAssetIdentifier(
            AssetIdentifierType.IP_ADDRESS, "192.0.2.10"
        ),
        canonical_asset_id="asset-001",
        criticality=AssetCriticality.HIGH,
        source_reference="asset-source:001",
    )


def _intelligence():
    return SimpleNamespace(
        cve_identifier=SimpleNamespace(value="CVE-2026-1234"),
        contract_version="1.0",
    )


def _status(value: str) -> HuntHypothesisReferenceResolutionStatus:
    return HuntHypothesisReferenceResolutionStatus(value)
