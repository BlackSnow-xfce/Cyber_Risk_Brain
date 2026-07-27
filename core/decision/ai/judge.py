from __future__ import annotations

from core.ai.reasoning_result import ReasoningResult


class Judge:
    """
    Final AI arbiter.

    Combines the Reviewer and Challenger
    into one trustworthy assessment.
    """

    def evaluate(
        self,
        reviewer: ReasoningResult,
        challenger: ReasoningResult,
    ) -> ReasoningResult:

        result = reviewer

        agree = (
            reviewer.verdict.lower()
            == "agree"
        )

        challenge_confidence = (
            challenger.confidence_review
        )

        if (
            not agree
            and challenge_confidence >= 90
        ):

            result.verdict = (
                "Needs Human Review"
            )

            result.counter_arguments.extend(

                challenger.counter_arguments

            )

            result.weaknesses.extend(

                challenger.weaknesses

            )

            result.missing_evidence.extend(

                challenger.missing_evidence

            )

            result.confidence_review = min(

                reviewer.confidence_review,

                challenger.confidence_review,

            )

            return result

        result.counter_arguments.extend(

            x
            for x in challenger.counter_arguments
            if x not in result.counter_arguments

        )

        result.weaknesses.extend(

            x
            for x in challenger.weaknesses
            if x not in result.weaknesses

        )

        result.missing_evidence.extend(

            x
            for x in challenger.missing_evidence
            if x not in result.missing_evidence

        )

        result.verdict = "Approved"

        result.confidence_review = (
            reviewer.confidence_review
            + challenger.confidence_review
        ) / 2

        return result
    