import type { Confidence } from "./Confidence";
import type { EntityStatus } from "./EntityStatus";
import type { Explainability } from "./Explainability";
import type { Severity } from "./Severity";
import type { Decision } from "@/decision";
import type { Inference } from "@/inference";
import type { Recommendation } from "@/recommendation";
import type {
    Correlation,
    Evidence,
    ReasoningChain,
} from "@/reasoning";

export interface Entity {
    id: string;
    title: string;
    description: string;
    severity: Severity;
    status: EntityStatus;
    riskScore: number;
    confidence: Confidence;
    recommendation?: Recommendation;
    explainability: Explainability;
    evidence: readonly Evidence[];
    correlations: readonly Correlation[];
    inference?: readonly Inference[];
    reasoning?: ReasoningChain;
    decision?: Decision;
}
