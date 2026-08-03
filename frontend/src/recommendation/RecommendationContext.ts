import type { Decision } from "@/decision";
import type { Entity } from "@/domain";
import type {
    Correlation,
    Evidence,
    ReasoningChain,
} from "@/reasoning";

export interface RecommendationContext {
    entity: Entity;
    evidence: readonly Evidence[];
    correlations: readonly Correlation[];
    reasoning: ReasoningChain;
    decision: Decision;
}
