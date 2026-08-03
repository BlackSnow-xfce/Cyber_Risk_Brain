import type { ReasoningChain } from "./ReasoningChain";
import type { ReasoningContext } from "./ReasoningContext";

export interface ReasoningEngine {
    reason: (context: ReasoningContext) => Promise<ReasoningChain>;
}
