import type { KnowledgeItem } from "./KnowledgeItem";

export interface KnowledgeRepository {
    getKnowledgeItems: () => readonly KnowledgeItem[];
}
