import type { ReasoningResult } from "./ReasoningResult";
import type { ReasoningStep } from "./ReasoningStep";

export interface ReasoningChain {
    id: string;
    entityId: string;
    steps: readonly ReasoningStep[];
    overallConfidence: number;
    result: ReasoningResult;
}
