export type DecisionStatus =
    | "waiting"
    | "running"
    | "completed"
    | "failed";

export type DecisionPriority =
    | "low"
    | "medium"
    | "high"
    | "critical";

export interface Decision {
    title: string;
    description: string;
    action: string;
}

export interface Evidence {
    id: string;
    title: string;
    value: string;
    confidence: number;
}

export interface Recommendation {
    id: string;
    title: string;
    description: string;
    automated: boolean;
}

export interface BusinessImpact {
    operations: string;
    financial: string;
    compliance: string;
    reputation: string;
}

export interface Explainability {
    reasoning: string;
    confidence: number;
}

export interface TimelineEvent {
    id: string;
    timestamp: string;
    title: string;
    description: string;
}

export interface DecisionMetadata {
    engine: string;
    model: string;
    version: string;
}

export interface DecisionResponse {
    id: string;

    createdAt: string;

    status: DecisionStatus;

    priority: DecisionPriority;

    decision: Decision;

    summary: string;

    confidence: number;

    evidence: Evidence[];

    recommendations: Recommendation[];

    businessImpact: BusinessImpact;

    explainability: Explainability;

    timeline: TimelineEvent[];

    metadata: DecisionMetadata;
}