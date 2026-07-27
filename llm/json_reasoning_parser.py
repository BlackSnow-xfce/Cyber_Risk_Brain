from __future__ import annotations

import json

from llm.reasoning_result import ReasoningResult


class JsonReasoningParser:
    """
    Converts the JSON response of an LLM
    into a ReasoningResult object.
    """

    def parse(
        self,
        response: str,
    ) -> ReasoningResult:

        try:

            data = json.loads(response)

        except Exception:

            return ReasoningResult(

                explanation=response,

                executive_summary=response,

                soc_summary=response,

                technical_summary=response,

                verdict="Parsing Failed",

                confidence_review=0.0,

                remediation_strategy="",

                strengths=[],

                weaknesses=[],

                missing_evidence=[],

                counter_arguments=[],

                assumptions=[],

                raw_response=response,

            )

        return ReasoningResult(

            explanation=data.get(
                "explanation",
                "",
            ),

            executive_summary=data.get(
                "executive_summary",
                "",
            ),

            soc_summary=data.get(
                "soc_summary",
                "",
            ),

            technical_summary=data.get(
                "technical_summary",
                "",
            ),

            verdict=data.get(
                "verdict",
                "Unknown",
            ),

            confidence_review=float(
                data.get(
                    "confidence_review",
                    0,
                )
            ),

            remediation_strategy=data.get(
                "remediation_strategy",
                "",
            ),

            strengths=data.get(
                "strengths",
                [],
            ),

            weaknesses=data.get(
                "weaknesses",
                [],
            ),

            missing_evidence=data.get(
                "missing_evidence",
                [],
            ),

            counter_arguments=data.get(
                "counter_arguments",
                [],
            ),

            assumptions=data.get(
                "assumptions",
                [],
            ),

            raw_response=response,

        )
    