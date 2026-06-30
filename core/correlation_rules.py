from core.event import SecurityEvent


class CorrelationRule:
    """
    Basisklasse für alle Korrelationsregeln.
    """

    name = "Base Rule"

    def match(self, events: list[SecurityEvent]) -> bool:
        raise NotImplementedError

    def description(self) -> str:
        return ""

class CredentialDumpingRule(CorrelationRule):

    name = "Credential Dumping"

    def match(self, events: list[SecurityEvent]) -> bool:

        has_lsass = False
        has_powershell = False

        for event in events:

            if event.event_type == "CredentialDumping":
                has_lsass = True

            if event.event_type == "PowerShell":
                has_powershell = True

        return has_lsass and has_powershell

    def description(self):
        return "PowerShell + LSASS Zugriff erkannt."
