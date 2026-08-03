import type { KnowledgeBinding } from "./KnowledgeBinding";

export interface KnowledgeBindingRepository {
    getBindings: () => readonly KnowledgeBinding[];
    getBindingsByEntityId: (
        entityId: string,
    ) => readonly KnowledgeBinding[];
    getBindingsByKnowledgeItemId: (
        knowledgeItemId: string,
    ) => readonly KnowledgeBinding[];
}
