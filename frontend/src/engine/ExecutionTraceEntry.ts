export type GeneratedArtifactType =
    | "Inference"
    | "Reasoning"
    | "Decision"
    | "Recommendation";

export interface GeneratedArtifactReference {
    type: GeneratedArtifactType;
    id: string;
}

export interface ExecutionTraceEntry {
    executedAt: string;
    executionOrder: number;
    ruleName: string;
    matched: boolean;
    skippedReason?: string;
    durationMs: number;
    generatedArtifacts: readonly GeneratedArtifactReference[];
}
