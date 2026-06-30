class MitreAnalyzer:

    def show_mitre_techniques(self, nodes):

        print("MITRE ATT&CK Techniques:")

        techniques = set()

        for node in nodes:

            techniques.add(node["mitre"])

        for technique in techniques:

            print(f"- {technique}")

    def mitre_detection_analysis(self, nodes):

        print("MITRE Detection Analysis:")

        for node in nodes:

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
