from dataclasses import dataclass
from enum import Enum


class ExposureReachability(str, Enum):
    DIRECT_EXTERNAL = "DIRECT_EXTERNAL"
    TRANSITIVE_EXTERNAL = "TRANSITIVE_EXTERNAL"
    AUTHENTICATED_EXTERNAL = "AUTHENTICATED_EXTERNAL"
    INTERNAL = "INTERNAL"
    LOCAL = "LOCAL"
    NOT_EXTERNALLY_REACHABLE = "NOT_EXTERNALLY_REACHABLE"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ExposureObservation:
    reachability: ExposureReachability
    evaluation_complete: bool

    @property
    def authoritative_value(self) -> bool | None:
        if not self.evaluation_complete or self.reachability is ExposureReachability.UNKNOWN:
            return None
        if self.reachability in {ExposureReachability.DIRECT_EXTERNAL, ExposureReachability.TRANSITIVE_EXTERNAL, ExposureReachability.AUTHENTICATED_EXTERNAL}:
            return True
        if self.reachability is ExposureReachability.NOT_EXTERNALLY_REACHABLE:
            return False
        return None
