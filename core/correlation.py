from collections import defaultdict

from core.event import SecurityEvent
from core.correlation_rules import CredentialDumpingRule


class CorrelationEngine:

    def __init__(self):
        self.events = []

        self.rules = [
            CredentialDumpingRule()
        ]

    def add_event(self, event: SecurityEvent):
        self.events.append(event)

    def correlate_by_asset(self):
        grouped = defaultdict(list)

        for event in self.events:
            grouped[event.asset].append(event)

        return grouped

    def detect_patterns(self):

        findings = []

        grouped = self.correlate_by_asset()

        for asset, events in grouped.items():

            for rule in self.rules:

                if rule.match(events):

                    findings.append(
                        {
                            "asset": asset,
                            "rule": rule.name,
                            "description": rule.description(),
                        }
                    )

        return findings
