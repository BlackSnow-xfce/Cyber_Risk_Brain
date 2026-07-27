from __future__ import annotations

from core.decision.decision_trace import DecisionTrace


class DecisionExplainer:
    """
    Generates human-readable explanations
    from a DecisionTrace.
    """

    def executive(
        self,
        trace: DecisionTrace,
    ) -> str:

        return (
            f"{trace.decision} "
            f"(Priority: {trace.priority}, "
            f"Risk Score: {trace.risk_score}) "
            f"based on {len(trace.reasons)} reasoning factors "
            f"and {len(trace.evidence)} supporting evidence items."
        )

    def soc(
        self,
        trace: DecisionTrace,
    ) -> str:

        evidence = ", ".join(

            evidence.name

            for evidence in trace.evidence

        )

        return (
            "SOC Assessment\n\n"
            f"Decision : {trace.decision}\n"
            f"Priority : {trace.priority}\n"
            f"Risk     : {trace.risk_score}\n"
            f"Evidence : {evidence}\n"
            f"Verdict  : {trace.ai_verdict}\n"
            f"Confidence : {trace.ai_confidence:.1f}%"
        )

    def technical(
        self,
        trace: DecisionTrace,
    ) -> str:

        lines = [

            "Technical Assessment",

            "",

            f"Decision : {trace.decision}",

            f"Priority : {trace.priority}",

            f"Risk Score : {trace.risk_score}",

            "",

            "Reasons:",

        ]

        for reason in trace.reasons:

            lines.append(

                f"- {reason.name}: "
                f"{reason.description}"

            )

        lines.append("")

        lines.append("Evidence:")

        for evidence in trace.evidence:

            lines.append(

                f"- {evidence.name}: "
                f"{evidence.description}"

            )

        if trace.counter_arguments:

            lines.append("")

            lines.append(
                "Counter Arguments:"
            )

            for argument in trace.counter_arguments:

                lines.append(
                    f"- {argument}"
                )

        if trace.recommendations:

            lines.append("")

            lines.append(
                "Recommendations:"
            )

            for recommendation in trace.recommendations:

                lines.append(

                    f"- {recommendation.title}"

                )

        return "\n".join(lines)
    