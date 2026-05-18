class RiskScorer:

    def __init__(self):
        self.weights = {
            "LOW": 1,
            "MEDIUM": 5,
            "HIGH": 8,
            "CRITICAL": 10
        }

    def calculate_score(self, severity):

        severity = severity.upper()

        return self.weights.get(severity, 0)
