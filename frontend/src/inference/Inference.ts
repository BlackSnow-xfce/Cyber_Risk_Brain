import type { InferenceResult } from "./InferenceResult";
import type { InferenceStrength } from "./InferenceStrength";
import type { InferenceType } from "./InferenceType";

export interface Inference {
    id: string;
    entityId: string;
    type: InferenceType;
    strength: InferenceStrength;
    title: string;
    description: string;
    confidence: number;
    supportingKnowledgeIds: readonly string[];
    supportingBindingIds: readonly string[];
    supportingEvidenceIds: readonly string[];
    supportingCorrelationIds: readonly string[];
    result: InferenceResult;
}
