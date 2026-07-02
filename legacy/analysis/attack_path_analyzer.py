class AttackPathAnalyzer:

    def show_attack_paths(self, edges):

        print("Attack Paths:")

        for edge in edges:

            source, target = edge

            print(f"{source} --> {target}")

    def find_exposed_paths(self, edges):

        print("Exposed Attack Chains:")

        for edge in edges:

            source, target = edge

            if source == "Internet":

                print(f"Internet --> {target}")

                for next_edge in edges:

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

    def detect_critical_paths(self, edges):

        print("Critical Attack Paths:")

        for edge in edges:

            source, target = edge

            if target == "Tier0 Asset":

                print(
                    f"Critical path detected: "
                    f"{source} --> {target}"
                )

    def crown_jewel_analysis(self, edges):

        print("Crown Jewel Analysis:")

        for edge in edges:

            source, target = edge

            if target == "Tier0 Asset":

                print(
                    f"Crown Jewel reachable through: "
                    f"{source}"
                )

                for second_edge in edges:

                    second_source, second_target = second_edge

                    if second_target == source:

                        print(
                            f"Attack chain: "
                            f"{second_source} --> "
                            f"{source} --> "
                            f"{target}"
                        )
