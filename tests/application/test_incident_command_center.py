from datetime import datetime, timezone

import pytest

from application import (
    IncidentCommandCenterIncidentNotFoundError,
    IncidentCommandCenterQueryService,
)
from core.explainability import CompletenessStatus
from core.incident_response import (
    AnalystNote,
    CanonicalAssetReference,
    DecisionVersionReference,
    EvidenceReference,
    FindingReference,
    IncidentActivity,
    IncidentActivityType,
    IncidentActivityDetail,
    IncidentActivityDetailType,
    IncidentPrincipalReference,
    IncidentPrincipalType,
    IncidentReferenceResolution,
    IncidentRelationship,
    IncidentRelationshipRole,
    IncidentLifecycleStatus,
    SecurityIncidentContext,
    ThreatIntelligenceReference,
)


NOW = datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc)
ACTOR = IncidentPrincipalReference(IncidentPrincipalType.USER, "analyst-001")


def test_projects_incident_references_notes_and_activity_without_domain_duplication() -> None:
    incident = _incident(with_all_references=True)
    finding = _finding_reference()
    asset = CanonicalAssetReference("asset-lab-001")
    ti = ThreatIntelligenceReference("CVE-2004-2687", "1.0")
    note = AnalystNote(
        note_id="note-1",
        note_version_id="note-1:v1",
        incident_id=incident.incident_id,
        author=ACTOR,
        content="Analyst context",
        created_at=NOW,
        version=1,
    )
    activity = IncidentActivity(
        activity_id="activity-1",
        incident_id=incident.incident_id,
        activity_type=IncidentActivityType.INCIDENT_CREATED,
        actor=ACTOR,
        occurred_at=NOW,
        sequence=1,
        description="Incident opened",
        details=(
            IncidentActivityDetail(IncidentActivityDetailType.REASON, "observed"),
        ),
    )
    resolutions = tuple(
        IncidentReferenceResolution(reference, CompletenessStatus.AVAILABLE, "owner:read")
        for reference in (finding, asset, ti)
    )

    projection = IncidentCommandCenterQueryService().project(
        incident,
        resolutions=resolutions,
        notes=(note,),
        activities=(activity,),
    )

    assert projection.incident is incident
    assert projection.findings == (finding,)
    assert projection.assets == (asset,)
    assert projection.threat_intelligence == (ti,)
    assert projection.notes == (note,)
    assert projection.activities == (activity,)
    assert projection.completeness.status is CompletenessStatus.AVAILABLE
    assert projection.missing_context == ()
    assert projection.sections[0].source_references == ("owner:read",)


def test_multiple_findings_and_assets_keep_explicit_source_order() -> None:
    finding_one = _finding_reference()
    finding_two = FindingReference(finding_id="finding-2", source="greenbone")
    asset_one = CanonicalAssetReference("asset-lab-001")
    asset_two = CanonicalAssetReference("asset-lab-002")
    incident = SecurityIncidentContext(
        incident_id="incident-1",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="soc",
        source_reference="soc:incident-1",
        title="Multiple references",
        created_at=NOW,
        updated_at=NOW,
        relationships=(
            IncidentRelationship(
                "r-f1", IncidentRelationshipRole.INVESTIGATION_CANDIDATE, finding_one
            ),
            IncidentRelationship(
                "r-f2", IncidentRelationshipRole.INVESTIGATION_CANDIDATE, finding_two
            ),
            IncidentRelationship(
                "r-a1", IncidentRelationshipRole.AFFECTED_ASSET, asset_one
            ),
            IncidentRelationship(
                "r-a2", IncidentRelationshipRole.AFFECTED_ASSET, asset_two
            ),
        ),
    )
    resolutions = tuple(
        IncidentReferenceResolution(reference, CompletenessStatus.AVAILABLE, "owner:read")
        for reference in (finding_one, finding_two, asset_one, asset_two)
    )

    projection = IncidentCommandCenterQueryService().project(
        incident,
        resolutions=resolutions,
    )

    assert projection.findings == (finding_one, finding_two)
    assert projection.assets == (asset_one, asset_two)
    assert projection.completeness.status is CompletenessStatus.NO_DATA


def test_decision_versions_and_evidence_remain_typed_references() -> None:
    finding = _finding_reference()
    evidence = EvidenceReference("evidence-1", "1.0")
    decision = DecisionVersionReference("decision-1", "version-2", "snapshot-2")
    incident = SecurityIncidentContext(
        incident_id="incident-1",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="soc",
        source_reference="soc:incident-1",
        title="Decision references",
        created_at=NOW,
        updated_at=NOW,
        relationships=(
            IncidentRelationship(
                "r-f", IncidentRelationshipRole.INVESTIGATION_CANDIDATE, finding
            ),
            IncidentRelationship(
                "r-e", IncidentRelationshipRole.SUPPORTING_EVIDENCE, evidence
            ),
            IncidentRelationship(
                "r-d", IncidentRelationshipRole.RELATED_DECISION, decision
            ),
        ),
    )
    resolutions = tuple(
        IncidentReferenceResolution(reference, CompletenessStatus.AVAILABLE, "owner:read")
        for reference in (finding, evidence, decision)
    )

    projection = IncidentCommandCenterQueryService().project(
        incident,
        resolutions=resolutions,
    )

    assert projection.evidence == (evidence,)
    assert projection.decisions == (decision,)
    assert projection.decisions[0].version_id == "version-2"


def test_missing_cross_domain_reference_is_no_data_and_not_invented() -> None:
    incident = _incident(with_finding=True)

    projection = IncidentCommandCenterQueryService().project(incident)

    assert projection.completeness.status is CompletenessStatus.NO_DATA
    assert "finding:greenbone:finding-1" in projection.missing_context
    assert projection.findings[0].finding_id == "finding-1"


def test_source_unavailable_is_preserved() -> None:
    incident = _incident(with_finding=True)
    reference = _finding_reference()

    projection = IncidentCommandCenterQueryService().project(
        incident,
        resolutions=(
            IncidentReferenceResolution(
                reference,
                CompletenessStatus.SOURCE_UNAVAILABLE,
                "finding-owner:unavailable",
            ),
        ),
    )

    assert projection.completeness.status is CompletenessStatus.SOURCE_UNAVAILABLE
    assert "finding:greenbone:finding-1:source_unavailable" in projection.missing_context


def test_no_relationships_are_not_applicable_and_empty_notes_activity_are_explicit() -> None:
    projection = IncidentCommandCenterQueryService().project(_incident())

    assert all(
        section.status is CompletenessStatus.NOT_APPLICABLE
        for section in projection.sections
    )
    assert "analyst-notes" in projection.missing_context
    assert "incident-activity" in projection.missing_context
    assert projection.completeness.status is CompletenessStatus.NO_DATA


def test_missing_incident_is_controlled() -> None:
    with pytest.raises(IncidentCommandCenterIncidentNotFoundError):
        IncidentCommandCenterQueryService().project(None)


def test_wrong_incident_owned_items_are_rejected() -> None:
    note = AnalystNote(
        note_id="note-1",
        note_version_id="note-1:v1",
        incident_id="other-incident",
        author=ACTOR,
        content="wrong owner",
        created_at=NOW,
        version=1,
    )

    with pytest.raises(ValueError, match="belong"):
        IncidentCommandCenterQueryService().project(_incident(), notes=(note,))


def test_projection_does_not_select_primary_or_execute_engines() -> None:
    incident = _incident(with_finding=True)
    projection = IncidentCommandCenterQueryService().project(incident)

    assert len(projection.findings) == 1
    assert not hasattr(projection, "primary_finding")
    assert not hasattr(projection, "risk_score")
    assert not hasattr(projection, "decision")
    assert not hasattr(projection, "correlation")


def _incident(
    *,
    with_finding: bool = False,
    with_all_references: bool = False,
) -> SecurityIncidentContext:
    relationships = ()
    if with_finding or with_all_references:
        relationships = [
            IncidentRelationship(
                relationship_id="relationship-finding-1",
                role=IncidentRelationshipRole.INVESTIGATION_CANDIDATE,
                target=_finding_reference(),
            ),
        ]
    if with_all_references:
        relationships.extend(
            (
                IncidentRelationship(
                    relationship_id="relationship-asset-1",
                    role=IncidentRelationshipRole.AFFECTED_ASSET,
                    target=CanonicalAssetReference("asset-lab-001"),
                ),
                IncidentRelationship(
                    relationship_id="relationship-ti-1",
                    role=IncidentRelationshipRole.THREAT_CONTEXT,
                    target=ThreatIntelligenceReference("CVE-2004-2687", "1.0"),
                ),
            )
        )
    relationships = tuple(relationships)
    return SecurityIncidentContext(
        incident_id="incident-1",
        lifecycle_status=IncidentLifecycleStatus.INVESTIGATING,
        source="soc",
        source_reference="soc:incident-1",
        title="Controlled incident",
        created_at=NOW,
        updated_at=NOW,
        relationships=relationships,
    )


def _finding_reference() -> FindingReference:
    return FindingReference(finding_id="finding-1", source="greenbone")
