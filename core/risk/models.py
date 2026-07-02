from dataclasses import dataclass
from typing import List


@dataclass
class RiskResult:

    asset: str

    score: int

    priority: str

    reasons: List[str]
