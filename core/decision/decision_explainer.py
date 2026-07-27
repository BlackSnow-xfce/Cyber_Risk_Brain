from __future__ import annotations

from core.decision.decision_trace import DecisionTrace


class DecisionExplainer:
    """
    Creates human-readable explanations from a DecisionTrace.

    Every explanation is generated from the
    same canonical DecisionTrace object.
    """

    def executive(
        self,
        trace: DecisionTrace,
    ) -> str:

        return (
            f"{trace.decision} "
            f"(Priority: {trace.priority}) "
            f"because {len(trace.evidence)} "
            f"high-confidence indicators support "
            f"this assessment."
        )

    def soc(
        self,
        trace: DecisionTrace,
    ) -> str:

        evidence = ", ".join(

            item.name

            for item in trace.evidence

        )

        return (
            "SOC Assessment:\n\n"
            f"Decision: {trace.decision}\n"
            f"Evidence: {evidence}\n"
            f"AI Verdict: {trace.ai_verdict}\n"
            f"Confidence: {trace.ai_confidence:.1f}%"
        )

    def technical(
        self,
        trace: DecisionTrace,
    ) -> str:

        lines = [

            "Technical Explanation",

            "",

            f"Decision: {trace.decision}",

            f"Priority: {trace.priority}",

            "",

            "Evidence:",

        ]

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

        return "\n".join(lines)
    