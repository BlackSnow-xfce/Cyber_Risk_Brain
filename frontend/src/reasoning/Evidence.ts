import type { EvidenceSource } from "./EvidenceSource";
import type { EvidenceType } from "./EvidenceType";

export interface Evidence {
    id: string;
    type: EvidenceType;
    source: EvidenceSource;
    title: string;
    description: string;
    confidence: number;
    timestamp: string;
    weight: number;
}
