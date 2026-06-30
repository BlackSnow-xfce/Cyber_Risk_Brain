from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Severity(Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


@dataclass
class SecurityEvent:
    source: str
    event_type: str
    title: str
    severity: Severity
    timestamp: datetime = field(default_factory=datetime.utcnow)

    asset: str | None = None
    user: str | None = None
    ip_address: str | None = None

    mitre_technique: str | None = None
    cve: str | None = None

    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_event: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "event_type": self.event_type,
            "title": self.title,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "asset": self.asset,
            "user": self.user,
            "ip_address": self.ip_address,
            "mitre_technique": self.mitre_technique,
            "cve": self.cve,
            "tags": self.tags,
            "metadata": self.metadata,
        }
