class DetectionAnalyzer:

    def detect_detection_gaps(self, nodes):

        print("Detection Gaps:")

        for node in nodes:

            if (
                node["exposed"]
                and not node["detection"]
            ):

                print(
                    f"No detection coverage "
                    f"for exposed asset: "
                    f"{node['name']}"
                )

    def detection_coverage_score(self, nodes):

        total = len(nodes)

        covered = 0

        for node in nodes:

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
