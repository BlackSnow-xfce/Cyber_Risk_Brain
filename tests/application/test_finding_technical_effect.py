from datetime import datetime, timezone

import pytest

from application.finding_technical_effect import FindingTechnicalEffectService, FindingTechnicalEffectStatus, TechnicalEffectLevel
from application.finding_threat_intelligence import FindingThreatIntelligenceEnrichment
from core.explainability import CompletenessStatus, ExplanationCompleteness, ExplanationProvenance
from core.threat_intelligence import (CisaKevInformation, CveIdentifier, CvssInformation,
    EpssInformation, FindingIntelligenceApplicability, FindingThreatIntelligence,
    IntelligenceFact, NvdIntelligence, VulnerabilityThreatIntelligence)


def _fact(value, source="nvd", observed_at=None):
    return IntelligenceFact(value, ExplanationCompleteness(CompletenessStatus.AVAILABLE,
        ExplanationProvenance(source, f"{source}:record")), observed_at)


def _unavailable(source):
    return IntelligenceFact(None, ExplanationCompleteness(CompletenessStatus.NO_DATA,
        ExplanationProvenance(source, f"{source}:none")))


def _enrichment(vector="CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:L/A:N", version="3.1", cve="CVE-2024-1234"):
    observed = datetime(2026, 1, 1, tzinfo=timezone.utc)
    vulnerability = VulnerabilityThreatIntelligence(
        CveIdentifier(cve), _fact(NvdIntelligence(summary="x")),
        _fact(CvssInformation(version, 8.0, vector), observed_at=observed),
        _fact(EpssInformation(.2), "epss"), _fact(CisaKevInformation(False), "cisa_kev"),
        _unavailable("cisa_kev"))
    return FindingThreatIntelligenceEnrichment("finding-1", "greenbone", "Finding", (
        FindingThreatIntelligence("finding-1", FindingIntelligenceApplicability.APPLICABLE, vulnerability),))


def test_cvss_v3_maps_cia_and_preserves_provenance_and_time():
    result = FindingTechnicalEffectService().project(_enrichment())
    assert result.status is FindingTechnicalEffectStatus.AVAILABLE
    assert (result.effects[0].confidentiality, result.effects[0].integrity, result.effects[0].availability) == (
        TechnicalEffectLevel.HIGH, TechnicalEffectLevel.LOW, TechnicalEffectLevel.NONE)
    assert result.effects[0].source_reference == "nvd:record"
    assert result.effects[0].observed_at == datetime(2026, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(("version", "vector"), [
    ("2.0", "AV:N/AC:L/Au:N/C:C/I:C/A:C"),
    ("4.0", "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H"),
    ("3.1", "CVSS:3.1/AV:N/C:X/I:H/A:H"),
    ("3.1", "CVSS:3.1/AV:N/C:H/I:H"),
])
def test_unsupported_or_malformed_vectors_are_unavailable(version, vector):
    result = FindingTechnicalEffectService().project(_enrichment(vector, version))
    assert result.status is FindingTechnicalEffectStatus.UNAVAILABLE
    assert result.effects == ()


def test_multiple_cves_remain_separate():
    first = _enrichment().relationships[0]
    second = _enrichment(cve="CVE-2024-5678").relationships[0]
    enrichment = FindingThreatIntelligenceEnrichment("finding-1", "greenbone", "Finding", (first, second))
    assert [item.cve_identifier for item in FindingTechnicalEffectService().project(enrichment).effects] == ["CVE-2024-1234", "CVE-2024-5678"]
