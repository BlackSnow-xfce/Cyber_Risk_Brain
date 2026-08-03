import type { KnowledgeBinding } from "./KnowledgeBinding";

export interface KnowledgeBindingCollection {
    readonly items: readonly KnowledgeBinding[];
    readonly entityId?: string;
}
