class RuleScorer:

    RULE_WEIGHTS = {

        "critical_attack_surface": 50,

        "internet_exposure": 20,

        "critical_vulnerability": 30,

        "public_exploit": 25,

        "high_cvss": 15,

        "medium_vulnerability": 10,

        "crown_jewel": 20

    }

    CRITICALITY_MULTIPLIER = {

        "Critical": 1.50,

        "High": 1.25,

        "Medium": 1.00,

        "Low": 0.75

    }

    def calculate(self, correlation, context):

        rule = correlation["type"]

        base_score = self.RULE_WEIGHTS.get(rule, 0)

        multiplier = self.CRITICALITY_MULTIPLIER.get(
            context.metadata.criticality,
            1.00
        )

        score = int(round(base_score * multiplier))

        return score
