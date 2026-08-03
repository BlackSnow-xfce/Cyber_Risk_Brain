export interface ReasoningStep {
    id: string;
    title: string;
    description: string;
    evidenceIds: readonly string[];
    correlationIds: readonly string[];
    confidence: number;
    order: number;
}
