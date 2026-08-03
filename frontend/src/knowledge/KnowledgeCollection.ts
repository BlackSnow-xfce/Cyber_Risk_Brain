import type { KnowledgeItem } from "./KnowledgeItem";

export interface KnowledgeCollection {
    items: readonly KnowledgeItem[];
}
