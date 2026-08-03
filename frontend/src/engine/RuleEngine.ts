import type { Decision } from "@/decision";
import type { Inference } from "@/inference";
import type { Recommendation } from "@/recommendation";
import type { ReasoningChain } from "@/reasoning";

import type { EngineContext } from "./EngineContext";
import type {
    GeneratedArtifactReference,
} from "./ExecutionTraceEntry";
import type { ExecutionTraceResult } from "./ExecutionTraceResult";
import type { RuleRegistry } from "./RuleRegistry";
import type { RuleResult } from "./RuleResult";

export interface EngineResult {
    ruleResults: readonly RuleResult[];
    inferences: readonly Inference[];
    reasoning: readonly ReasoningChain[];
    decisions: readonly Decision[];
    recommendations: readonly Recommendation[];
    executionTrace: ExecutionTraceResult;
}

export class RuleEngine {
    constructor(private readonly registry: RuleRegistry) {}

    evaluate(context: EngineContext): EngineResult {
        const rules = [...this.registry.rules]
            .filter((rule) => rule.enabled)
            .sort((left, right) => left.priority - right.priority);
        const executionStartedAt = Date.now();
        const ruleResults = rules.map((rule, index) => {
            const result = rule.evaluate(context);
            const generatedArtifacts: GeneratedArtifactReference[] = [
                ...result.generatedInferenceIds.map((id) => ({
                    type: "Inference" as const,
                    id,
                })),
                ...result.generatedReasoningIds.map((id) => ({
                    type: "Reasoning" as const,
                    id,
                })),
                ...(result.generatedDecisionId
                    ? [
                          {
                              type: "Decision" as const,
                              id: result.generatedDecisionId,
                          },
                      ]
                    : []),
                ...(result.generatedRecommendationId
                    ? [
                          {
                              type: "Recommendation" as const,
                              id: result.generatedRecommendationId,
                          },
                      ]
                    : []),
            ];

            return {
                ...result,
                executedAt: new Date(
                    executionStartedAt + index * 1000,
                ).toISOString(),
                executionOrder: index + 1,
                ruleName: rule.name,
                durationMs: 1,
                generatedArtifacts,
            };
        });

        return {
            ruleResults,
            inferences: ruleResults.flatMap(
                (result) => result.generatedInferences,
            ),
            reasoning: ruleResults.flatMap(
                (result) => result.generatedReasoning,
            ),
            decisions: ruleResults.flatMap((result) =>
                result.generatedDecision === undefined
                    ? []
                    : [result.generatedDecision],
            ),
            recommendations: ruleResults.flatMap((result) =>
                result.generatedRecommendation === undefined
                    ? []
                    : [result.generatedRecommendation],
            ),
            executionTrace: { entries: ruleResults },
        };
    }
}
