from application.finding_model_egress import (
    FindingModelEgressProjector,
)
from core.ai_authorization import AIResourceType
from core.ai_context import AIContextClassification
from core.ai_egress import (
    AIModelEgressDecision,
    AIModelEgressField,
    AIModelEgressPolicy,
    AIModelEgressPurpose,
)
from core.models import UniversalFinding


def finding():
    return UniversalFinding(
        id="finding-1",
        source="greenbone",
        title="Observed finding",
        vendor_severity="HIGH",
        business_criticality="CRITICAL",
        asset="asset-1",
        exposed=True,
        detection_available=True,
        threat_intel_match=True,
        mitre_tactic="initial-access",
        owner="analyst",
        remediation="sensitive remediation detail",
        cve_identifiers=("CVE-2024-0001",),
    )


def policy(*fields):
    return AIModelEgressPolicy(
        purpose=AIModelEgressPurpose.FINDING_EXPLANATION,
        resource_type=AIResourceType.FINDING,
        permitted_classifications=frozenset({AIContextClassification.INTERNAL}),
        allowed_fields=frozenset(fields),
        decision=AIModelEgressDecision.ALLOW,
        policy_source_reference="policy:finding-explanation",
    )


def test_positive_allowlist_projection_contains_only_allowed_fields():
    payload = FindingModelEgressProjector.project(
        finding(),
        policy(
            AIModelEgressField.FINDING_TITLE,
            AIModelEgressField.FINDING_VENDOR_SEVERITY,
        ),
    )
    assert payload is not None
    assert payload.as_dict() == {
        "finding.title": "Observed finding",
        "finding.vendor_severity": "HIGH",
    }


def test_future_and_sensitive_finding_fields_are_not_serialized():
    payload = FindingModelEgressProjector.project(
        finding(), policy(AIModelEgressField.FINDING_TITLE)
    )
    assert payload is not None
    assert payload.as_dict() == {"finding.title": "Observed finding"}
    assert "remediation" not in payload.as_dict()
    assert "cve_identifiers" not in payload.as_dict()
    assert "asset" not in payload.as_dict()


def test_policy_can_withhold_supported_field():
    payload = FindingModelEgressProjector.project(
        finding(), policy(AIModelEgressField.FINDING_VENDOR_SEVERITY)
    )
    assert payload is not None
    assert payload.as_dict() == {"finding.vendor_severity": "HIGH"}


def test_unsupported_policy_field_fails_closed_without_dynamic_lookup():
    unsupported = AIModelEgressPolicy(
        purpose=AIModelEgressPurpose.FINDING_EXPLANATION,
        resource_type=AIResourceType.FINDING,
        permitted_classifications=frozenset({AIContextClassification.INTERNAL}),
        allowed_fields=frozenset({AIModelEgressField.FINDING_ID}),
        decision=AIModelEgressDecision.ALLOW,
        policy_source_reference="policy:unsupported",
    )
    assert FindingModelEgressProjector.project(finding(), unsupported) is None


def test_wrong_policy_context_fails_closed():
    wrong_purpose = AIModelEgressPolicy(
        purpose=AIModelEgressPurpose.FINDING_EXPLANATION,
        resource_type=AIResourceType.INCIDENT,
        permitted_classifications=frozenset({AIContextClassification.INTERNAL}),
        allowed_fields=frozenset({AIModelEgressField.FINDING_TITLE}),
        decision=AIModelEgressDecision.ALLOW,
        policy_source_reference="policy:wrong-resource",
    )
    assert FindingModelEgressProjector.project(finding(), wrong_purpose) is None


def test_no_finding_repository_or_provider_access_and_no_mutation():
    original = finding()
    payload = FindingModelEgressProjector.project(
        original, policy(AIModelEgressField.FINDING_TITLE)
    )
    assert payload is not None
    assert original.remediation == "sensitive remediation detail"
    assert original.cve_identifiers == ("CVE-2024-0001",)
    assert not hasattr(FindingModelEgressProjector, "reader")
