from core.threat_intel.merger import ThreatIntelMerger
from core.threat_intel.models import ThreatIntelResult


def main():

    merger = ThreatIntelMerger()

    epss_result = ThreatIntelResult(
        cve_id="CVE-2024-0001",
        epss_score=0.91,
        epss_percentile=0.99,
    )

    epss_result.add_source(
        name="EPSS",
        available=True,
        data={"epss": "0.91", "percentile": "0.99"},
    )

    kev_result = ThreatIntelResult(
        cve_id="CVE-2024-0001",
        is_kev=True,
        exploitation_observed=True,
        ransomware_usage_observed=False,
        kev_vendor_project="Example Vendor",
        kev_product="Example Product",
        kev_vulnerability_name="Example Vulnerability",
    )

    kev_result.add_source(
        name="CISA KEV",
        available=True,
        data={"cveID": "CVE-2024-0001"},
    )

    results = merger.merge_many(
        cves=["CVE-2024-0001", "CVE-2024-0002"],
        partial_results=[
            epss_result,
            kev_result,
        ],
    )

    result = results["CVE-2024-0001"]

    assert result.cve_id == "CVE-2024-0001"
    assert result.epss_score == 0.91
    assert result.epss_percentile == 0.99
    assert result.is_kev is True
    assert result.known_exploited is True
    assert result.exploitation_observed is True
    assert result.ransomware_usage_observed is False
    assert result.kev_vendor_project == "Example Vendor"
    assert result.kev_product == "Example Product"
    assert result.kev_vulnerability_name == "Example Vulnerability"
    assert len(result.sources) == 2

    empty_result = results["CVE-2024-0002"]

    assert empty_result.cve_id == "CVE-2024-0002"
    assert empty_result.epss_score is None
    assert empty_result.is_kev is False
    assert empty_result.sources == []

    print("ThreatIntelMerger test successful.")


if __name__ == "__main__":
    main()
