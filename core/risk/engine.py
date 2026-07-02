from .models import RiskResult
from .scoring import RuleScorer


class RiskEngine:

    def __init__(self):

        self.scorer = RuleScorer()

    def calculate(self, asset_name, context, correlations):

        score = 0

        reasons = []

        for correlation in correlations:

            score += self.scorer.calculate(
                correlation,
                context
            )

            reasons.append(correlation["reason"])

        score = min(score, 100)

        if score >= 90:

            priority = "Critical"

        elif score >= 70:

            priority = "High"

        elif score >= 40:

            priority = "Medium"

        else:

            priority = "Low"

        return RiskResult(

            asset=asset_name,

            score=score,

            priority=priority,

            reasons=sorted(set(reasons))

        )
