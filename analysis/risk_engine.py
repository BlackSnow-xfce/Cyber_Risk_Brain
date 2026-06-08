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

    def calculate_business_risk(self, node):

        score = 0

        if node["criticality"] == "CRITICAL":
            score += 5

        elif node["criticality"] == "HIGH":
            score += 4

        elif node["criticality"] == "MEDIUM":
            score += 2

        else:
            score += 1

        if node["exposed"]:
            score += 3

        if not node["detection"]:
            score += 2

        if node["threat_intel"]:
            score += 3

        if score >= 12:
            return "CRITICAL"

        elif score >= 8:
            return "HIGH"

        elif score >= 4:
            return "MEDIUM"

        return "LOW"