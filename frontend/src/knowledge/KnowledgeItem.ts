import type { KnowledgeReference } from "./KnowledgeReference";
import type { KnowledgeSource } from "./KnowledgeSource";
import type { KnowledgeType } from "./KnowledgeType";

export interface KnowledgeItem {
    id: string;
    type: KnowledgeType;
    source: KnowledgeSource;
    title: string;
    description: string;
    reference: KnowledgeReference;
    confidence: number;
    tags: readonly string[];
}
