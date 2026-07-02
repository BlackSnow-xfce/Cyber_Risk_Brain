from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ThreatIntelSource:
    name: str
    available: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ThreatIntelResult:
    cve_id: str

    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None

    # NVD
    description: Optional[str] = None
    published: Optional[str] = None
    last_modified: Optional[str] = None

    cvss_score: Optional[float] = None
    cvss_severity: Optional[str] = None
    cvss_version: Optional[str] = None
    cvss_vector: Optional[str] = None

    attack_vector: Optional[str] = None
    attack_complexity: Optional[str] = None
    privileges_required: Optional[str] = None
    user_interaction: Optional[str] = None
    scope: Optional[str] = None

    confidentiality: Optional[str] = None
    integrity: Optional[str] = None
    availability: Optional[str] = None

    vendor: Optional[str] = None
    product: Optional[str] = None

    cwe: Optional[str] = None
    cwe_ids: List[str] = field(default_factory=list)

    cpes: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    is_kev: bool = False

    kev_vendor_project: Optional[str] = None
    kev_product: Optional[str] = None
    kev_vulnerability_name: Optional[str] = None
    kev_date_added: Optional[str] = None
    kev_short_description: Optional[str] = None
    kev_required_action: Optional[str] = None
    kev_due_date: Optional[str] = None
    kev_known_ransomware_campaign_use: Optional[str] = None
    kev_notes: Optional[str] = None

    exploit_available: Optional[bool] = None
    exploitation_observed: Optional[bool] = None
    ransomware_usage_observed: Optional[bool] = None

    sources: List[ThreatIntelSource] = field(default_factory=list)

    @property
    def cve(self) -> str:
        return self.cve_id

    @property
    def known_exploited(self) -> bool:
        return self.is_kev

    @property
    def high_epss(self) -> bool:
        return (
            self.epss_score is not None
            and self.epss_score >= 0.3
        )

    @property
    def very_high_epss(self) -> bool:
        return (
            self.epss_score is not None
            and self.epss_score >= 0.7
        )

    def add_source(
        self,
        name: str,
        available: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        self.sources.append(
            ThreatIntelSource(
                name=name,
                available=available,
                data=data or {},
                error=error,
            )
        )

    @property
    def has_epss(self) -> bool:
        return self.epss_score is not None

    @property
    def has_kev(self) -> bool:
        return self.is_kev

    @property
    def has_active_exploitation_signal(self) -> bool:
        return bool(
            self.is_kev
            or self.exploitation_observed
            or self.ransomware_usage_observed
        )

    @property
    def priority_label(self) -> str:
        if self.is_kev:
            return "critical"

        if self.epss_score is not None and self.epss_score >= 0.7:
            return "high"

        if self.epss_score is not None and self.epss_score >= 0.3:
            return "medium"

        return "low"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
