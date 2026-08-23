from datetime import datetime, timezone
from types import SimpleNamespace

from application import (
    IncidentReferenceResolutionService,
)
from application.incident_command_center import IncidentCommandCenterQueryService
from core.enterprise_context import (
    AssetContext,
    AssetCriticality,
    AssetIdentifierType,
    ObservedAssetIdentifier,
)
from core.explainability import CompletenessStatus, ExplanationProvenance
from core.incident_response import (
    CanonicalAssetReference,
    EvidenceReference,
    FindingReference,
    IncidentLifecycleStatus,
    IncidentRelationship,
    IncidentRelationshipRole,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)
from core.models import UniversalFinding


class _Findings:
    def __init__(self, findings):
        self._findings = findings

    def get_findings(self):
        return self._findings


class _Assets:
    def __init__(self, result):
        self.result = result

    def resolve_canonical_asset(self, canonical_asset_id):
        return self.result


class _ThreatIntelligence:
    def __init__(self, result=None):
        self.result = result

    def get_by_cve(self, cve):
        if self.result is None:
            from application.threat_intelligence import ThreatIntelligenceNotFoundError
            raise ThreatIntelligenceNotFoundError("missing")
        return self.result


def _incident(*references):
    roles = {
        FindingReference: IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
        CanonicalAssetReference: IncidentRelationshipRole.AFFECTED_ASSET,
        ThreatIntelligenceReference: IncidentRelationshipRole.THREAT_CONTEXT,
        EvidenceReference: IncidentRelationshipRole.SUPPORTING_EVIDENCE,
    }
    return SecurityIncidentContext(
        incident_id="incident-1",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="test",
        source_reference="test:incident-1",
        title="Incident",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        relationships=tuple(
            IncidentRelationship(f"r-{index}", roles[type(reference)], reference)
            for index, reference in enumerate(references)
        ),
    )


def test_authoritative_finding_asset_and_ti_resolution_are_independent():
    asset = AssetContext(
        ObservedAssetIdentifier(AssetIdentifierType.IP_ADDRESS, "172.18.0.19"),
        "asset-lab-metasploitable2-001",
        AssetCriticality.HIGH,
        "asset-context:asset-lab-metasploitable2-001",
    )
    intelligence = _intelligence()
    refs = (
        FindingReference("finding-1", "greenbone"),
        CanonicalAssetReference("asset-lab-metasploitable2-001"),
        ThreatIntelligenceReference("CVE-2004-2687", "1.0"),
    )
    resolver = IncidentReferenceResolutionService(
        _Findings([UniversalFinding("finding-1", "greenbone", "title", "HIGH", "HIGH", "asset", True, True, True, None, None, None)]),
        _Assets(asset),
        _ThreatIntelligence(intelligence),
    )
    results = resolver.resolve(_incident(*refs))
    assert [item.status for item in results] == [
        CompletenessStatus.AVAILABLE,
        CompletenessStatus.AVAILABLE,
        CompletenessStatus.AVAILABLE,
    ]


def test_missing_source_and_evidence_remain_fail_closed():
    refs = (
        FindingReference("missing", "greenbone"),
        EvidenceReference("correlation:finding-1:CVE-2004-2687", "1.0"),
    )
    resolver = IncidentReferenceResolutionService(
        _Findings([]),
        _Assets(None),
        _ThreatIntelligence(),
    )
    results = resolver.resolve(_incident(*refs))
    assert [item.status for item in results] == [
        CompletenessStatus.NO_DATA,
        CompletenessStatus.NO_DATA,
    ]


def test_command_center_consumes_resolver_results_for_completeness():
    finding = FindingReference("finding-1", "greenbone")
    resolver = IncidentReferenceResolutionService(
        _Findings([UniversalFinding("finding-1", "greenbone", "title", "HIGH", "HIGH", "asset", True, True, True, None, None, None)]),
        _Assets(None),
        _ThreatIntelligence(),
    )
    projection = IncidentCommandCenterQueryService(resolver).project(
        _incident(finding)
    )
    assert projection.sections[0].status is CompletenessStatus.AVAILABLE
    assert projection.sections[0].source_references == (
        "finding-query:greenbone:finding-1",
    )


def test_missing_resolver_never_implies_available():
    finding = FindingReference("finding-1", "greenbone")
    resolver = IncidentReferenceResolutionService(None, None, None)
    result = resolver.resolve(_incident(finding))[0]
    assert result.status is CompletenessStatus.NO_DATA


def _intelligence():
    provenance = ExplanationProvenance("test", "test:ti")
    return SimpleNamespace(
        nvd=SimpleNamespace(
            completeness=SimpleNamespace(
                status=CompletenessStatus.AVAILABLE,
                provenance=provenance,
            )
        )
    )
