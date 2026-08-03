import type { KnowledgeBindingStrength } from "./KnowledgeBindingStrength";
import type { KnowledgeBindingType } from "./KnowledgeBindingType";

export interface KnowledgeBinding {
    id: string;
    knowledgeItemId: string;
    entityId: string;
    evidenceId?: string;
    type: KnowledgeBindingType;
    strength: KnowledgeBindingStrength;
    confidence: number;
    rationale: string;
    createdAt: string;
}
