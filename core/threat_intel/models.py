from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ThreatIntelResult:
    cve: str
    epss_score: Optional[float] = None
    epss_percentile: Optional[float] = None
    known_exploited: bool = False
    exploit_available: bool = False
    sources: List[str] = field(default_factory=list)

    @property
    def has_epss(self) -> bool:
        return self.epss_score is not None

    @property
    def high_epss(self) -> bool:
        return self.epss_score is not None and self.epss_score >= 0.7

    @property
    def very_high_epss(self) -> bool:
        return self.epss_score is not None and self.epss_score >= 0.9
