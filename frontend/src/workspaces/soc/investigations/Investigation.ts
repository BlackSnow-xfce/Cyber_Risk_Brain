import type { Entity } from "@/domain";
import type { Recommendation } from "@/recommendation";

export interface Investigation extends Entity {
    assignedAnalyst: string;
    lastUpdated: string;
    timeline: string;
    relatedFindings: string;
    analystNotes: string;
    recommendation: Recommendation;
}
