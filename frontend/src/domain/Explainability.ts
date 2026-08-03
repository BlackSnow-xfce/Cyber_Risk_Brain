import type { Confidence } from "./Confidence";

export interface Explainability {
    reason: string;
    confidence: Confidence;
    businessImpact: string;
    mitre: readonly string[];
    kev: boolean | null;
    epss: number | null;
    attackPath: readonly string[];
}
