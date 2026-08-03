import type { Rule } from "../Rule";
import type { RulePack } from "../RulePack";
import { unmatchedRuleResult } from "../RuleResult";
import {
    buildInferenceResult,
    createInference,
    getBoundKnowledge,
} from "../RuleUtilities";

const kevAndInternetFacingRule: Rule = {
    id: "kev-internet-facing",
    name: "KEV and internet-facing exposure",
    description:
        "Identifies known exploited vulnerabilities with internet-facing evidence.",
    priority: 10,
    enabled: true,
    evaluate: (context) => {
        const kev = getBoundKnowledge(context, "KEV");
        const internetEvidence = context.evidence.filter(
            (evidence) => evidence.type === "Internet Facing",
        );
        if (kev.bindingIds.length === 0 || internetEvidence.length === 0) {
            return unmatchedRuleResult(
                "No bound KEV knowledge or internet-facing evidence.",
            );
        }

        const confidence = Math.min(
            ...internetEvidence.map((evidence) => evidence.confidence),
            ...context.knowledgeBindings
                .filter((binding) => kev.bindingIds.includes(binding.id))
                .map((binding) => binding.confidence),
        );
        return buildInferenceResult(
            createInference(
                context,
                "kev-internet-facing",
                "PUBLIC_EXPLOIT_AVAILABLE",
                "Known exploited vulnerability is internet facing",
                "KEV knowledge and internet-facing evidence apply to the same entity.",
                confidence,
                kev.knowledgeIds,
                kev.bindingIds,
                internetEvidence.map((evidence) => evidence.id),
                [],
            ),
        );
    },
};

export const kevRulePack: RulePack = {
    id: "kev",
    name: "KEV Rules",
    description: "Rules based on known exploited vulnerability knowledge.",
    version: "1.0.0",
    enabled: true,
    rules: [kevAndInternetFacingRule],
};
