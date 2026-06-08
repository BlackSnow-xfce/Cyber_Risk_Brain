from dataclasses import dataclass
from typing import Optional


@dataclass
class Finding:
    name: str
    severity: str
    exposed: bool
    criticality: str
    detection: bool
    threat_intel: bool
    mitre: str
    owner: str
    sla_days: int


@dataclass
class UniversalFinding:
    id: str
    source: str
    title: str
    vendor_severity: str
    business_criticality: str
    asset: str
    exposed: bool
    detection_available: bool
    threat_intel_match: bool
    mitre_tactic: Optional[str]
    owner: Optional[str]
    remediation: Optional[str]