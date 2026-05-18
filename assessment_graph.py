class AssessmentGraph:

    def __init__(self):
        self.nodes = []
        self.edges = []

    def add_node(
        self,
        node,
        severity="LOW",
        exposed=False,
        criticality="LOW",
        detection=False,
        threat_intel=False,
        mitre="UNKNOWN"
    ):

        self.nodes.append({
            "name": node,
            "severity": severity,
            "exposed": exposed,
            "criticality": criticality,
            "detection": detection,
            "threat_intel": threat_intel,
            "mitre": mitre
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
            threat_intel = node["threat_intel"]

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

            if threat_intel:
                score += 5

        score += len(self.edges)

        for edge in self.edges:

            source, target = edge

            if target == "Tier0 Asset":
                score += 15

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
    def show_attack_paths(self):

        print("Attack Paths:")

        for edge in self.edges:

            source, target = edge

            print(f"{source} --> {target}")

    def find_exposed_paths(self):

        print("Exposed Attack Chains:")

        for edge in self.edges:

            source, target = edge

            if source == "Internet":

                print(f"Internet --> {target}")

                for next_edge in self.edges:

                    next_source, next_target = next_edge

                    if next_source == target:

                        chain = f"Internet --> {target} --> {next_target}"

                        print(chain)

                        if next_target == "Internal Admin Panel":

                            print("Potential lateral movement detected")

    def detect_critical_paths(self):

        print("Critical Attack Paths:")

        for edge in self.edges:

            source, target = edge

            if target == "Tier0 Asset":

                print(f"Critical path detected: {source} --> {target}")

    def prioritize_findings(self):

        print("Prioritized Findings:")

        for node in self.nodes:

            severity = node["severity"]
            exposed = node["exposed"]
            criticality = node["criticality"]

            if (
                severity == "CRITICAL"
                and exposed
                and criticality == "CRITICAL"
            ):

                print(f"HIGHEST PRIORITY: {node['name']}")

            elif severity == "HIGH" and exposed:

                print(f"HIGH PRIORITY: {node['name']}")

            else:

                print(f"NORMAL PRIORITY: {node['name']}")

    def detect_detection_gaps(self):

        print("Detection Gaps:")

        for node in self.nodes:

            if node["exposed"] and not node["detection"]:

                print(
                    f"No detection coverage for exposed asset: {node['name']}"
                )

    def detection_coverage_score(self):

        total = len(self.nodes)

        covered = 0

        for node in self.nodes:

            if node["detection"]:
                covered += 1

        coverage = (covered / total) * 100

        print(f"Detection Coverage: {coverage:.2f}%")

        if coverage < 50:
            print("WARNING: Poor detection coverage")

        elif coverage < 80:
            print("Detection coverage could be improved")

        else:
            print("Detection coverage looks good")

    def executive_summary(self):

        print("Executive Summary")

        print(f"Total Findings: {len(self.nodes)}")

        print(f"Total Attack Paths: {len(self.edges)}")

        risk = self.calculate_risk()

        print(f"Overall Risk Score: {risk}")

        print(f"Overall Risk Level: {self.get_risk_level()}")

        exposed_assets = 0

        for node in self.nodes:

            if node["exposed"]:
                exposed_assets += 1

        print(f"Internet Exposed Assets: {exposed_assets}")

        critical_findings = 0

        for node in self.nodes:

            if node["severity"] == "CRITICAL":
                critical_findings += 1

        print(f"Critical Findings: {critical_findings}")

        if risk >= 50:
            print("Immediate remediation recommended")

        elif risk >= 25:
            print("High remediation priority")

        else:
            print("Environment currently stable")
