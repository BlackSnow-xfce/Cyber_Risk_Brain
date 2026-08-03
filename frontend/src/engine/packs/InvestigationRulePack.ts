import type { ReasoningChain } from "@/reasoning";

import type { Rule } from "../Rule";
import type { RulePack } from "../RulePack";
import { unmatchedRuleResult } from "../RuleResult";

const evidenceConfidenceRule: Rule = {
    id: "evidence-confidence",
    name: "Evidence confidence",
    description:
        "Creates a higher-confidence reasoning result when at least three evidence items are present.",
    priority: 40,
    enabled: true,
    evaluate: (context) => {
        if (context.evidence.length < 3) {
            return unmatchedRuleResult(
                "Fewer than three evidence items are available.",
            );
        }

        const baseConfidence =
            context.entity.reasoning?.overallConfidence ??
            context.entity.confidence.score;
        const confidence = Math.min(100, baseConfidence + 5);
        const reasoningId = `reasoning-${context.entity.id}-evidence-confidence`;
        const reasoning: ReasoningChain = {
            id: reasoningId,
            entityId: context.entity.id,
            steps: [
                {
                    id: `${reasoningId}-step-1`,
                    title: "Multiple evidence items available",
                    description:
                        "At least three evidence items support the entity context.",
                    evidenceIds: context.evidence.map((evidence) => evidence.id),
                    correlationIds: [],
                    confidence,
                    order: 1,
                },
            ],
            overallConfidence: confidence,
            result: {
                summary:
                    "Multiple evidence items increase confidence in the analysis context.",
                confidence,
                findings: [
                    `${context.evidence.length} evidence items are available.`,
                ],
            },
        };

        return {
            ...unmatchedRuleResult(),
            matched: true,
            generatedReasoningIds: [reasoningId],
            generatedReasoning: [reasoning],
        };
    },
};

export const investigationRulePack: RulePack = {
    id: "investigation",
    name: "Investigation Rules",
    description: "Rules for investigation evidence and validation context.",
    version: "1.0.0",
    enabled: true,
    rules: [evidenceConfidenceRule],
};
