from .models import ThreatIntelResult


class ThreatIntelHelper:

    @staticmethod
    def results(context):
        return context.threat_intel.values()

    @staticmethod
    def get(context, cve: str) -> ThreatIntelResult | None:
        return context.threat_intel.get(cve.upper())

    @staticmethod
    def has_high_epss(context) -> bool:
        return any(
            intel.high_epss
            for intel in context.threat_intel.values()
        )

    @staticmethod
    def has_very_high_epss(context) -> bool:
        return any(
            intel.very_high_epss
            for intel in context.threat_intel.values()
        )

    @staticmethod
    def high_epss_count(context) -> int:
        return sum(
            1
            for intel in context.threat_intel.values()
            if intel.high_epss
        )

    @staticmethod
    def very_high_epss_count(context) -> int:
        return sum(
            1
            for intel in context.threat_intel.values()
            if intel.very_high_epss
        )

    @staticmethod
    def max_epss(context) -> float:
        scores = [
            intel.epss_score
            for intel in context.threat_intel.values()
            if intel.epss_score is not None
        ]

        return max(scores, default=0.0)

    @staticmethod
    def has_known_exploited(context) -> bool:
        return any(
            intel.known_exploited
            for intel in context.threat_intel.values()
        )

    @staticmethod
    def known_exploited_count(context) -> int:
        return sum(
            1
            for intel in context.threat_intel.values()
            if intel.known_exploited
        )
