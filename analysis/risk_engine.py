class RiskEngine:

    def calculate_risk(self, nodes):

        score = 0

        for node in nodes:

            if node["criticality"] == "CRITICAL":
                score += 10

            elif node["criticality"] == "HIGH":
                score += 7

            elif node["criticality"] == "MEDIUM":
                score += 4

            else:
                score += 1

        return score

    def get_risk_level(self, risk):

        if risk >= 20:
            return "CRITICAL"

        elif risk >= 10:
            return "HIGH"

        elif risk >= 5:
            return "MEDIUM"

        return "LOW"
