from application import (
    FindingAssetContextResolutionStatus,
    FindingAssetContextUseCase,
)
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.models import UniversalFinding


class StubFindings:
    def __init__(self, finding: UniversalFinding) -> None:
        self.finding = finding

    def get_findings(self) -> list[UniversalFinding]:
        return [self.finding]


class RecordingAssetContexts:
    def __init__(self, context: AssetContext | None) -> None:
        self.context = context
        self.calls: list[ObservedAssetIdentifier] = []

    def resolve(
        self,
        observed_identifier: ObservedAssetIdentifier,
    ) -> AssetContext | None:
        self.calls.append(observed_identifier)
        if (
            self.context is not None
            and self.context.observed_identifier == observed_identifier
        ):
            return self.context
        return None


def test_known_ip_resolves_explicit_canonical_context_and_provenance() -> None:
    contexts = RecordingAssetContexts(lab_context())
    use_case = FindingAssetContextUseCase(
        StubFindings(finding(vendor_severity="Critical")),
        contexts,
    )

    result = use_case.resolve("finding-001")

    assert result.status is FindingAssetContextResolutionStatus.RESOLVED
    assert result.observed_identifier == lab_identifier()
    assert result.asset_context is not None
    assert result.asset_context.canonical_asset_id == (
        "asset-lab-metasploitable2-001"
    )
    assert result.asset_context.criticality is AssetCriticality.LOW
    assert result.asset_context.source_reference == (
        "product-owner:metasploitable2-lab-classification"
    )
    assert contexts.calls == [lab_identifier()]


def test_unknown_ip_returns_not_found_without_default_context() -> None:
    contexts = RecordingAssetContexts(lab_context())
    result = FindingAssetContextUseCase(
        StubFindings(finding(asset="192.0.2.99")),
        contexts,
    ).resolve("finding-001")

    assert result.status is FindingAssetContextResolutionStatus.NOT_FOUND
    assert result.observed_identifier == identifier("192.0.2.99")
    assert result.asset_context is None


def test_hostname_is_unresolved_without_ip_validation_error() -> None:
    contexts = RecordingAssetContexts(lab_context())
    result = FindingAssetContextUseCase(
        StubFindings(finding(asset="scanner-host.example.test")),
        contexts,
    ).resolve("finding-001")

    assert result.status is FindingAssetContextResolutionStatus.NOT_FOUND
    assert result.observed_identifier is None
    assert result.asset_context is None
    assert contexts.calls == []


def test_unclassifiable_identifier_is_unresolved_without_context_lookup() -> None:
    contexts = RecordingAssetContexts(lab_context())
    result = FindingAssetContextUseCase(
        StubFindings(finding(asset="not a supported identifier")),
        contexts,
    ).resolve("finding-001")

    assert result.status is FindingAssetContextResolutionStatus.NOT_FOUND
    assert result.observed_identifier is None
    assert result.asset_context is None
    assert contexts.calls == []


def test_missing_identifier_is_controlled_and_skips_context_resolution() -> None:
    contexts = RecordingAssetContexts(lab_context())
    result = FindingAssetContextUseCase(
        StubFindings(finding(asset="  ")),
        contexts,
    ).resolve("finding-001")

    assert result.status is (
        FindingAssetContextResolutionStatus.MISSING_IDENTIFIER
    )
    assert result.observed_identifier is None
    assert result.asset_context is None
    assert contexts.calls == []


def test_identifier_type_is_explicit_and_unsupported_type_cannot_match() -> None:
    result = FindingAssetContextUseCase(
        StubFindings(finding()),
        RecordingAssetContexts(lab_context()),
    ).resolve("finding-001")

    assert result.observed_identifier is not None
    assert result.observed_identifier.identifier_type is (
        AssetIdentifierType.IP_ADDRESS
    )
    try:
        AssetIdentifierType("hostname")
    except ValueError:
        pass
    else:
        raise AssertionError("Unsupported identifier type must be rejected.")


def test_resolution_does_not_derive_from_finding_or_ti_signals() -> None:
    result = FindingAssetContextUseCase(
        StubFindings(
            finding(
                vendor_severity="Critical",
                cve_identifiers=("CVE-2004-2687",),
                threat_intel_match=True,
            )
        ),
        RecordingAssetContexts(lab_context()),
    ).resolve("finding-001")

    assert result.asset_context is not None
    assert result.asset_context.criticality is AssetCriticality.LOW
    assert not hasattr(result, "cvss")
    assert not hasattr(result, "epss")
    assert not hasattr(result, "kev")
    assert not hasattr(result, "risk")
    assert not hasattr(result, "decision")


def test_distcc_ipv4_resolution_remains_unchanged() -> None:
    result = FindingAssetContextUseCase(
        StubFindings(
            finding(
                asset="172.18.0.19",
                cve_identifiers=("CVE-2004-2687",),
            )
        ),
        RecordingAssetContexts(lab_context()),
    ).resolve("finding-001")

    assert result.status is FindingAssetContextResolutionStatus.RESOLVED
    assert result.observed_identifier == lab_identifier()
    assert result.asset_context == lab_context()


def identifier(value: str) -> ObservedAssetIdentifier:
    return ObservedAssetIdentifier(
        identifier_type=AssetIdentifierType.IP_ADDRESS,
        value=value,
    )


def lab_identifier() -> ObservedAssetIdentifier:
    return identifier("172.18.0.19")


def lab_context() -> AssetContext:
    return AssetContext(
        observed_identifier=lab_identifier(),
        canonical_asset_id="asset-lab-metasploitable2-001",
        criticality=AssetCriticality.LOW,
        source_reference=(
            "product-owner:metasploitable2-lab-classification"
        ),
    )


def finding(
    *,
    asset: str = "172.18.0.19",
    vendor_severity: str = "High",
    cve_identifiers: tuple[str, ...] = (),
    threat_intel_match: bool = False,
) -> UniversalFinding:
    return UniversalFinding(
        id="finding-001",
        source="greenbone",
        title="DistCC RCE Vulnerability (CVE-2004-2687)",
        vendor_severity=vendor_severity,
        business_criticality="UNKNOWN",
        asset=asset,
        exposed=False,
        detection_available=False,
        threat_intel_match=threat_intel_match,
        mitre_tactic=None,
        owner=None,
        remediation=None,
        cve_identifiers=cve_identifiers,
    )
