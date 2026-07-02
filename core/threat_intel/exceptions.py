class ThreatIntelError(Exception):
    pass


class ThreatIntelHTTPError(ThreatIntelError):
    pass


class ThreatIntelTimeoutError(ThreatIntelError):
    pass


class ThreatIntelProviderError(ThreatIntelError):
    pass


class ThreatIntelJSONError(ThreatIntelError):
    pass
