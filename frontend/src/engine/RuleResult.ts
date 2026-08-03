import type { Decision } from "@/decision";
import type { Inference } from "@/inference";
import type { Recommendation } from "@/recommendation";
import type { ReasoningChain } from "@/reasoning";

import type { ExecutionTraceEntry } from "./ExecutionTraceEntry";

export interface RuleResult extends ExecutionTraceEntry {
    generatedInferenceIds: readonly string[];
    generatedReasoningIds: readonly string[];
    generatedDecisionId: string | undefined;
    generatedRecommendationId: string | undefined;
    generatedInferences: readonly Inference[];
    generatedReasoning: readonly ReasoningChain[];
    generatedDecision: Decision | undefined;
    generatedRecommendation: Recommendation | undefined;
}

export const unmatchedRuleResult = (skippedReason?: string): RuleResult => ({
    executedAt: "",
    executionOrder: 0,
    ruleName: "",
    matched: false,
    skippedReason,
    durationMs: 0,
    generatedArtifacts: [],
    generatedInferenceIds: [],
    generatedReasoningIds: [],
    generatedDecisionId: undefined,
    generatedRecommendationId: undefined,
    generatedInferences: [],
    generatedReasoning: [],
    generatedDecision: undefined,
    generatedRecommendation: undefined,
});
