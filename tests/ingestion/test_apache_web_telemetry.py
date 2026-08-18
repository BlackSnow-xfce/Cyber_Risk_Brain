from datetime import datetime, timezone

from application import (
    IncidentObservation,
    IncidentWebEvidenceAssociationService,
)
from core.decision.models import EvidenceKind, EvidenceType
from core.enterprise_context import (
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.explainability import CompletenessStatus
from core.security_observation import (
    ApacheAccessObservation,
    ApacheErrorObservation,
    WebTelemetryRecordType,
)
from ingestion import ApacheWebTelemetryParser

ACCESS_LINE = (
    '172.18.0.14 - - [16/Aug/2026:15:52:52 +0000] '
    '"GET /file://etc/passwd%00.jpg HTTP/1.1" 404 465 "-" '
    '"Mozilla/5.0 [en] (X11, U; OpenVAS-VT 23.50.0)"'
)
ERROR_LINE = (
    "[Sun Aug 16 15:52:42.833968 2026] [core:error] [pid 291] "
    "[client 172.18.0.14:35489] AH00126: Invalid URI in request "
    r"GET ///////../../../../etc/passwd/ HTTP/1.1"
)
ACCESS_SOURCE = "docker:dvwa:/var/log/apache2/access.log#line=1"
ERROR_SOURCE = "docker:dvwa:/var/log/apache2/error.log#line=1"


def test_real_access_line_maps_observed_fields_to_source_evidence() -> None:
    result = parse_access()

    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.record is not None
    assert result.record.record_type is WebTelemetryRecordType.ACCESS
    assert result.record.observed_at == datetime(
        2026,
        8,
        16,
        15,
        52,
        52,
        tzinfo=timezone.utc,
    )
    observation = result.record.observation
    assert isinstance(observation, ApacheAccessObservation)
    assert observation.client_ip == "172.18.0.14"
    assert observation.http_method == "GET"
    assert observation.request_target == "/file://etc/passwd%00.jpg"
    assert observation.http_version == "HTTP/1.1"
    assert observation.response_status == 404
    assert observation.response_size == 465
    assert observation.referer is None


def test_real_error_line_maps_observed_fields_to_source_evidence() -> None:
    result = parse_error()

    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.record is not None
    assert result.record.record_type is WebTelemetryRecordType.ERROR
    observation = result.record.observation
    assert isinstance(observation, ApacheErrorObservation)
    assert observation.module == "core"
    assert observation.severity == "error"
    assert observation.process_id == 291
    assert observation.client_ip == "172.18.0.14"
    assert observation.source_port == 35489
    assert observation.error_code == "AH00126"
    assert "Invalid URI in request" in observation.message


def test_openvas_user_agent_remains_only_an_observed_value() -> None:
    record = parse_access().record

    assert record is not None
    observation = record.observation
    assert isinstance(observation, ApacheAccessObservation)
    assert observation.user_agent == (
        "Mozilla/5.0 [en] (X11, U; OpenVAS-VT 23.50.0)"
    )
    for classification in ("scanner", "attacker", "threat_actor"):
        assert not hasattr(observation, classification)


def test_passwd_like_request_creates_no_exploitation_assertion() -> None:
    record = parse_access().record

    assert record is not None
    assert "/etc/passwd" in record.observation.request_target
    assert record.evidence.description == (
        "Observed Apache web telemetry without interpretation."
    )
    for interpretation in (
        "path_traversal",
        "exploitation_successful",
        "initial_access",
        "cve_exploited",
        "risk",
    ):
        assert not hasattr(record, interpretation)
        assert not hasattr(record.observation, interpretation)


def test_malformed_access_line_is_controlled_no_data() -> None:
    result = ApacheWebTelemetryParser().parse_access(
        "not an apache access line",
        observed_target_asset=target_asset(),
        source_reference=ACCESS_SOURCE,
    )

    assert result.record is None
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert "unsupported-sha256=" in (
        result.completeness.provenance.source_reference
    )


def test_malformed_error_line_is_controlled_no_data() -> None:
    result = ApacheWebTelemetryParser().parse_error(
        "[invalid] error",
        observed_target_asset=target_asset(),
        source_reference=ERROR_SOURCE,
    )

    assert result.record is None
    assert result.completeness.status is CompletenessStatus.NO_DATA


def test_evidence_identity_is_deterministic_for_identical_input() -> None:
    first = parse_access().record
    second = parse_access().record

    assert first is not None
    assert second is not None
    assert first.evidence.identifier == second.evidence.identifier
    assert first == second


def test_client_ip_and_observed_target_asset_remain_separate() -> None:
    record = parse_access().record

    assert record is not None
    assert record.observation.client_ip == "172.18.0.14"
    assert record.observed_target_asset == target_asset()
    assert record.observed_target_asset.value == "172.18.0.18"
    assert record.observation.client_ip != record.observed_target_asset.value


def test_web_telemetry_is_canonical_source_not_derived_evidence() -> None:
    record = parse_error().record

    assert record is not None
    assert record.evidence.evidence_type is EvidenceType.WEB_TELEMETRY
    assert record.evidence.kind is EvidenceKind.SOURCE
    assert record.evidence.contract_version == "1.0"
    assert record.evidence.provenance is not None
    assert record.evidence.provenance.input_references == ()


def test_repeated_ingestion_preserves_value_and_provenance() -> None:
    first = parse_error().record
    second = parse_error().record

    assert first == second
    assert first is not None
    assert first.completeness.provenance.source_reference == (
        first.evidence.provenance.source_reference
    )


def test_incident_association_uses_target_without_causality() -> None:
    access = parse_access().record
    error = parse_error().record
    assert access is not None
    assert error is not None
    incident = IncidentObservation(
        incident_id="incident-dvwa-web-001",
        source="controlled-lab-soc-observation",
        observed_at=datetime(2026, 8, 16, 15, 53, tzinfo=timezone.utc),
        observed_asset_identifier=target_asset(),
    )

    result = IncidentWebEvidenceAssociationService().associate(
        incident,
        (access, error),
    )

    assert result.completeness.status is CompletenessStatus.AVAILABLE
    assert result.evidence == (access, error)
    assert result.evidence_references == (
        access.evidence.identifier,
        error.evidence.identifier,
    )
    assert result.missing_context == ()
    for forbidden in (
        "caused_incident",
        "confirmed_initial_access",
        "exploitation_successful",
        "risk",
        "decision",
        "response_action",
    ):
        assert not hasattr(result, forbidden)


def test_incident_association_does_not_use_client_as_target() -> None:
    record = parse_access().record
    assert record is not None
    incident = IncidentObservation(
        incident_id="incident-other-target",
        source="controlled-lab-soc-observation",
        observed_at=datetime(2026, 8, 16, 15, 53, tzinfo=timezone.utc),
        observed_asset_identifier=ObservedAssetIdentifier(
            AssetIdentifierType.IP_ADDRESS,
            "172.18.0.14",
        ),
    )

    result = IncidentWebEvidenceAssociationService().associate(
        incident,
        (record,),
    )

    assert result.evidence == ()
    assert result.completeness.status is CompletenessStatus.NO_DATA
    assert result.missing_context == ("web-incident-source-evidence",)


def parse_access():
    return ApacheWebTelemetryParser().parse_access(
        ACCESS_LINE,
        observed_target_asset=target_asset(),
        source_reference=ACCESS_SOURCE,
    )


def parse_error():
    return ApacheWebTelemetryParser().parse_error(
        ERROR_LINE,
        observed_target_asset=target_asset(),
        source_reference=ERROR_SOURCE,
    )


def target_asset() -> ObservedAssetIdentifier:
    return ObservedAssetIdentifier(
        AssetIdentifierType.IP_ADDRESS,
        "172.18.0.18",
    )
