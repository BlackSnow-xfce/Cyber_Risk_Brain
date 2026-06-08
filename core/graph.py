class AssessmentGraph:

    def __init__(self):

        self.nodes = []
        self.edges = []

    def add_node(self, node, **kwargs):

        self.nodes.append({
            "name": node,
            **kwargs
        })

    def add_edge(self, source, target):

        self.edges.append((source, target))

    def show_graph(self):

        print("Nodes:", self.nodes)
        print("Edges:", self.edges)

    def calculate_risk(self):

        score = 0

        for node in self.nodes:

            if node["criticality"] == "CRITICAL":
                score += 10

            elif node["criticality"] == "HIGH":
                score += 7

            elif node["criticality"] == "MEDIUM":
                score += 4

            else:
                score += 1

        return score

    def get_risk_level(self):

        risk = self.calculate_risk()

        if risk >= 20:
            return "CRITICAL"

        elif risk >= 10:
            return "HIGH"

        elif risk >= 5:
            return "MEDIUM"

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

                        chain = (
                            f"Internet --> "
                            f"{target} --> "
                            f"{next_target}"
                        )

                        print(chain)

                        if next_target == "Internal Admin Panel":

                            print(
                                "Potential lateral movement detected"
                            )

    def detect_critical_paths(self):

        print("Critical Attack Paths:")

        for edge in self.edges:

            source, target = edge

            if target == "Tier0 Asset":

                print(
                    f"Critical path detected: "
                    f"{source} --> {target}"
                )

    def prioritize_findings(self):

        print("Prioritized Findings:")

        for node in self.nodes:

            criticality = node["criticality"]
            detection = node["detection"]

            if (
                criticality == "CRITICAL"
                and not detection
            ):

                print(
                    f"HIGHEST PRIORITY: "
                    f"{node['name']}"
                )

            elif criticality == "HIGH":

                print(
                    f"HIGH PRIORITY: "
                    f"{node['name']}"
                )

            else:

                print(
                    f"NORMAL PRIORITY: "
                    f"{node['name']}"
                )

    def detect_detection_gaps(self):

        print("Detection Gaps:")

        for node in self.nodes:

            if (
                node["exposed"]
                and not node["detection"]
            ):

                print(
                    f"No detection coverage for exposed asset: "
                    f"{node['name']}"
                )

    def detection_coverage_score(self):

        total = len(self.nodes)

        covered = 0

        for node in self.nodes:

            if node["detection"]:
                covered += 1

        coverage = (covered / total) * 100

        print(
            f"Detection Coverage: "
            f"{coverage:.2f}%"
        )

        if coverage < 50:

            print(
                "WARNING: Poor detection coverage"
            )

        elif coverage < 80:

            print(
                "Detection coverage could be improved"
            )

        else:

            print(
                "Detection coverage looks good"
            )

    def executive_summary(self):

        print("Executive Summary")

        print(f"Total Findings: {len(self.nodes)}")

        print(f"Total Attack Paths: {len(self.edges)}")

        risk = self.calculate_risk()

        print(f"Overall Risk Score: {risk}")

        print(
            f"Overall Risk Level: "
            f"{self.get_risk_level()}"
        )

        exposed_assets = 0

        for node in self.nodes:

            if node["exposed"]:
                exposed_assets += 1

        print(
            f"Internet Exposed Assets: "
            f"{exposed_assets}"
        )

        critical_findings = 0

        for node in self.nodes:

            if node["criticality"] == "CRITICAL":
                critical_findings += 1

        print(
            f"Critical Findings: "
            f"{critical_findings}"
        )

        if risk >= 50:

            print(
                "Immediate remediation recommended"
            )

        elif risk >= 25:

            print(
                "High remediation priority"
            )

        else:

            print(
                "Environment currently stable"
            )

    def show_mitre_techniques(self):

        print("MITRE ATT&CK Techniques:")

        techniques = set()

        for node in self.nodes:

            techniques.add(node["mitre"])

        for technique in techniques:

            print(f"- {technique}")

    def mitre_detection_analysis(self):

        print("MITRE Detection Analysis:")

        for node in self.nodes:

            technique = node["mitre"]

            if node["detection"]:

                print(
                    f"{technique}: "
                    f"Detection coverage available"
                )

            else:

                print(
                    f"{technique}: "
                    f"NO detection coverage"
                )

    def crown_jewel_analysis(self):

        print("Crown Jewel Analysis:")

        for edge in self.edges:

            source, target = edge

            if target == "Tier0 Asset":

                print(
                    f"Crown Jewel reachable through: "
                    f"{source}"
                )

                for second_edge in self.edges:

                    second_source, second_target = second_edge

                    if second_target == source:

                        print(
                            f"Attack chain: "
                            f"{second_source} --> "
                            f"{source} --> "
                            f"{target}"
                        )

    def remediation_recommendations(self):

        print("Remediation Recommendations:")

        for node in self.nodes:

            if (
                node["criticality"] == "CRITICAL"
                and node["exposed"]
            ):

                print(
                    f"Immediate remediation required: "
                    f"{node['name']}"
                )

            elif (
                node["criticality"] == "HIGH"
                and not node["detection"]
            ):

                print(
                    f"Improve detection coverage for: "
                    f"{node['name']}"
                )

            elif node["threat_intel"]:

                print(
                    f"Monitor active threat exposure: "
                    f"{node['name']}"
                )
