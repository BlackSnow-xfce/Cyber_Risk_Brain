from datetime import date, datetime, timezone

import pytest

from core.explainability import (
    CompletenessStatus,
    ExplanationCompleteness,
    ExplanationProvenance,
)
from core.threat_intelligence import (
    CisaKevInformation,
    CveIdentifier,
    CvssInformation,
    EpssInformation,
    ExploitationEvidence,
    FindingIntelligenceApplicability,
    FindingThreatIntelligence,
    IntelligenceFact,
    NvdIntelligence,
    VulnerabilityThreatIntelligence,
)

OBSERVED_AT = datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc)


def provenance(source: str, reference: str) -> ExplanationProvenance:
    return ExplanationProvenance(
        source_type=source,
        source_reference=reference,
    )


def available(value, source: str, reference: str):
    return IntelligenceFact(
        value=value,
        completeness=ExplanationCompleteness(
            status=CompletenessStatus.AVAILABLE,
            provenance=provenance(source, reference),
        ),
        observed_at=OBSERVED_AT,
    )


def test_complete_cve_intelligence_retains_values_and_provenance() -> None:
    intelligence = VulnerabilityThreatIntelligence(
        cve_identifier=CveIdentifier("cve-2026-12345"),
        nvd=available(
            NvdIntelligence(
                summary="Controlled vulnerability description.",
                published_at=OBSERVED_AT,
                last_modified_at=OBSERVED_AT,
            ),
            "nvd",
            "nvd:CVE-2026-12345",
        ),
        cvss=available(
            CvssInformation(
                version="3.1",
                base_score=9.8,
                vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H",
                severity="CRITICAL",
            ),
            "nvd",
            "nvd:CVE-2026-12345#cvss-v3.1",
        ),
        epss=available(
            EpssInformation(probability=0.91, percentile=0.99),
            "epss",
            "epss:CVE-2026-12345:2026-08-17",
        ),
        cisa_kev=available(
            CisaKevInformation(
                known_exploited=True,
                date_added=date(2026, 8, 1),
                required_action="Apply vendor mitigations.",
                due_date=date(2026, 8, 22),
            ),
            "cisa_kev",
            "cisa-kev:CVE-2026-12345",
        ),
        exploitation_evidence=available(
            (
                ExploitationEvidence(
                    evidence_type="known_exploited_catalog",
                    description="The CVE is present in CISA KEV.",
                    provenance=provenance(
                        "cisa_kev",
                        "cisa-kev:CVE-2026-12345",
                    ),
                    observed_at=OBSERVED_AT,
                ),
            ),
            "cisa_kev",
            "cisa-kev:CVE-2026-12345",
        ),
    )

    assert intelligence.cve_identifier.value == "CVE-2026-12345"
    assert intelligence.cvss.value.base_score == 9.8
    assert intelligence.epss.value.probability == 0.91
    assert intelligence.cisa_kev.value.known_exploited is True
    assert intelligence.nvd.provenance.source_type == "nvd"
    assert intelligence.epss.provenance.source_type == "epss"
    assert intelligence.cisa_kev.provenance.source_type == "cisa_kev"
    assert (
        intelligence.exploitation_evidence.value[0].provenance.source_reference
        == "cisa-kev:CVE-2026-12345"
    )


@pytest.mark.parametrize(
    "status",
    [
        CompletenessStatus.NO_DATA,
        CompletenessStatus.SOURCE_UNAVAILABLE,
        CompletenessStatus.NOT_EVALUATED,
        CompletenessStatus.NOT_APPLICABLE,
    ],
)
def test_missing_intelligence_has_no_sentinel_value(
    status: CompletenessStatus,
) -> None:
    completeness = ExplanationCompleteness(
        status=status,
        provenance=provenance("epss", "epss:source"),
    )

    fact = IntelligenceFact[float](value=None, completeness=completeness)
    assert fact.value is None
    assert fact.completeness.status == status

    with pytest.raises(ValueError, match="sentinel"):
        IntelligenceFact(value=0.0, completeness=completeness)


def test_finding_without_cve_is_not_applicable_without_artificial_mapping() -> None:
    result = FindingThreatIntelligence(
        finding_id="configuration-finding-001",
        applicability=FindingIntelligenceApplicability.NOT_APPLICABLE,
    )

    assert result.vulnerability is None

    unevaluated = FindingThreatIntelligence(
        finding_id="finding-002",
        applicability=FindingIntelligenceApplicability.NOT_EVALUATED,
    )
    assert unevaluated.vulnerability is None

