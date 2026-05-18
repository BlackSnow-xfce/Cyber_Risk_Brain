class AssessmentGraph:

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(
        self,
        node,
        severity="LOW",
        exposed=False,
        criticality="LOW"
    ):

        self.nodes.append({
            "name": node,
            "severity": severity,
            "exposed": exposed,
            "criticality": criticality
        })        

    def add_edge(self, source, target):
        self.edges.append((source, target))

    def show_graph(self):
        print("Nodes:", self.nodes)
        print("Edges:", self.edges)

    def calculate_risk(self):

        score = 0

        for node in self.nodes:

            severity = node["severity"]
            exposed = node["exposed"]

            if severity == "CRITICAL":
                score += 10

            elif severity == "HIGH":
                score += 7

            elif severity == "MEDIUM":
                score += 4

            else:
                score += 1

            if exposed:
                score += 3

        score += len(self.edges)

        return score

    def get_risk_level(self):

        risk = self.calculate_risk()

        if risk >= 25:
            return "CRITICAL"

        elif risk >= 15:
            return "HIGH"

        elif risk >= 5:
            return "MEDIUM"

        return "LOW"
