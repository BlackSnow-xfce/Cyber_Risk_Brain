from __future__ import annotations

from core.decision.ai.reasoning_result import (
    ReasoningResult,
)


class Judge:
    """
    Final AI arbiter.

    Merges Reviewer and Challenger into one
    trusted reasoning result.
    """

    def evaluate(
        self,
        reviewer: ReasoningResult,
        challenger: ReasoningResult,
    ) -> ReasoningResult:

        result = reviewer

        self._merge(result, challenger)

        agree = (
            reviewer.verdict.lower() == "agree"
        )

        if (
            not agree
            and challenger.confidence_review >= 90
        ):

            result.verdict = (
                "Needs Human Review"
            )

            result.confidence_review = min(
                reviewer.confidence_review,
                challenger.confidence_review,
            )

            result.executive_summary = (
                "PredatorAI identified conflicting "
                "AI assessments. Human validation "
                "is recommended."
            )

            return result

        result.verdict = "Approved"

        result.confidence_review = round(
            (
                reviewer.confidence_review
                + challenger.confidence_review
            )
            / 2,
            1,
        )

        return result

    def _merge(
        self,
        target: ReasoningResult,
        source: ReasoningResult,
    ) -> None:

        self._merge_unique(
            target.strengths,
            source.strengths,
        )

        self._merge_unique(
            target.weaknesses,
            source.weaknesses,
        )

        self._merge_unique(
            target.counter_arguments,
            source.counter_arguments,
        )

        self._merge_unique(
            target.missing_evidence,
            source.missing_evidence,
        )

        self._merge_unique(
            target.assumptions,
            source.assumptions,
        )

        self._merge_unique(
            target.reviewer_notes,
            source.reviewer_notes,
        )

        self._merge_unique(
            target.challenger_notes,
            source.challenger_notes,
        )

    @staticmethod
    def _merge_unique(
        target: list[str],
        source: list[str],
    ) -> None:

        for item in source:

            if item not in target:

                target.append(item)

                