import type { Entity } from "@/domain";
import type { KnowledgeBinding, KnowledgeItem } from "@/knowledge";
import type { Correlation, Evidence } from "@/reasoning";

export interface InferenceContext {
    entity: Entity;
    knowledge: readonly KnowledgeItem[];
    knowledgeBindings: readonly KnowledgeBinding[];
    evidence: readonly Evidence[];
    correlations: readonly Correlation[];
}
