from dataclasses import dataclass


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
