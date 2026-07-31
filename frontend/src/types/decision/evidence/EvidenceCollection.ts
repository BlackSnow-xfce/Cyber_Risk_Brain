import type { Evidence } from "./Evidence";

export interface EvidenceCollection {
    items: Evidence[];

    coverage: number;

    quality: number;

    sourceCount: number;

    duplicateCount: number;
}