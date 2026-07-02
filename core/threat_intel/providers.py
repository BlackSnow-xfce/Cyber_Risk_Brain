from abc import ABC, abstractmethod
from typing import Iterable, List

from .models import ThreatIntelResult


class ThreatIntelProvider(ABC):

    @abstractmethod
    def lookup(self, cves: Iterable[str]) -> List[ThreatIntelResult]:
        pass
