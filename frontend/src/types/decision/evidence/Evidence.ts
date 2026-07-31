import type { EvidenceType } from "../enums";

export interface Evidence {
    id: string;

    type: EvidenceType;

    source: string;

    sourceReference: string;

    summary: string;

    timestamp: string;

    confidence: number;

    weight: number;

    facts: string[];

    snapshot?: string;
}