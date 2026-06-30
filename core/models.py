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

from dataclasses import dataclass, field
from typing import List, Optional
from uuid import uuid4


@dataclass
class Asset:
    id: str = field(default_factory=lambda: str(uuid4()))
    hostname: str = ""
    ip: str = ""
    mac: str = ""
    os: str = ""
    internet_facing: bool = False
    criticality: str = "medium"
    tags: List[str] = field(default_factory=list)


@dataclass
class Software:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    vendor: str = ""
    version: str = ""


@dataclass
class Vulnerability:
    id: str = field(default_factory=lambda: str(uuid4()))
    cve: Optional[str] = None
    title: str = ""
    severity: str = "unknown"
    cvss: float = 0.0
    exploit_available: bool = False


@dataclass
class NormalizedFinding:
    asset: Asset
    software: Optional[Software] = None
    vulnerability: Optional[Vulnerability] = None
    source: str = ""
    port: Optional[int] = None
    protocol: Optional[str] = None
