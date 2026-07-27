from __future__ import annotations

from llm.reasoning_result import ReasoningResult


class Consensus:
    """
    Combines the Reviewer and Challenger
    into a single final AI assessment.
    """

    def combine(
        self,
        reviewer: ReasoningResult,
        challenger: ReasoningResult,
    ) -> ReasoningResult:

        strengths = list(reviewer.strengths)

        for item in challenger.strengths:

            if item not in strengths:

                strengths.append(item)

        weaknesses = list(reviewer.weaknesses)

        for item in challenger.weaknesses:

            if item not in weaknesses:

                weaknesses.append(item)

        missing = list(reviewer.missing_evidence)

        for item in challenger.missing_evidence:

            if item not in missing:

                missing.append(item)

        counter = list(reviewer.counter_arguments)

        for item in challenger.counter_arguments:

            if item not in counter:

                counter.append(item)

        assumptions = list(reviewer.assumptions)

        for item in challenger.assumptions:

            if item not in assumptions:

                assumptions.append(item)

        confidence = (
            reviewer.confidence_review +
            challenger.confidence_review
        ) / 2

        verdict = reviewer.verdict

        if reviewer.verdict != challenger.verdict:

            verdict = (
                f"{reviewer.verdict} "
                f"(challenged)"
            )

        return ReasoningResult(

            explanation=reviewer.explanation,

            executive_summary=reviewer.executive_summary,

            soc_summary=reviewer.soc_summary,

            technical_summary=reviewer.technical_summary,

            remediation_strategy=reviewer.remediation_strategy,

            verdict=verdict,

            confidence_review=confidence,

            strengths=strengths,

            weaknesses=weaknesses,

            missing_evidence=missing,

            counter_arguments=counter,

            assumptions=assumptions,

            raw_response=reviewer.raw_response,

        )
    