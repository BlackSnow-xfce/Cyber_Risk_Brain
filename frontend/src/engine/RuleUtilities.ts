import type { Inference, InferenceType } from "@/inference";

import type { EngineContext } from "./EngineContext";
import type { RuleResult } from "./RuleResult";
import { unmatchedRuleResult } from "./RuleResult";

export const buildInferenceResult = (
    inference: Inference,
): RuleResult => ({
    ...unmatchedRuleResult(),
    matched: true,
    generatedInferenceIds: [inference.id],
    generatedInferences: [inference],
});

export const getBoundKnowledge = (
    context: EngineContext,
    knowledgeType: string,
) => {
    const knowledgeIds = new Set(
        context.knowledge
            .filter((item) => item.type === knowledgeType)
            .map((item) => item.id),
    );
    const bindings = context.knowledgeBindings.filter(
        (binding) =>
            binding.entityId === context.entity.id &&
            knowledgeIds.has(binding.knowledgeItemId),
    );

    return {
        knowledgeIds: [
            ...new Set(bindings.map((binding) => binding.knowledgeItemId)),
        ],
        bindingIds: bindings.map((binding) => binding.id),
    };
};

export const createInference = (
    context: EngineContext,
    ruleId: string,
    type: InferenceType,
    title: string,
    description: string,
    confidence: number,
    supportingKnowledgeIds: readonly string[],
    supportingBindingIds: readonly string[],
    supportingEvidenceIds: readonly string[],
    supportingCorrelationIds: readonly string[],
): Inference => ({
    id: `inference-${context.entity.id}-${ruleId}`,
    entityId: context.entity.id,
    type,
    strength:
        confidence >= 90 ? "Strong" : confidence >= 70 ? "Medium" : "Weak",
    title,
    description,
    confidence,
    supportingKnowledgeIds,
    supportingBindingIds,
    supportingEvidenceIds,
    supportingCorrelationIds,
    result: {
        summary: description,
        confidence,
        findings: [title],
    },
});
