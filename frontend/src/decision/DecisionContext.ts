import type { Entity } from "@/domain";
import type {
    Correlation,
    Evidence,
    ReasoningChain,
} from "@/reasoning";

export interface DecisionContext {
    entity: Entity;
    evidence: readonly Evidence[];
    correlations: readonly Correlation[];
    reasoning: ReasoningChain;
}
