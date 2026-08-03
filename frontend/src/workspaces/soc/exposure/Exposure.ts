import type { Entity } from "@/domain";
import type { Recommendation } from "@/recommendation";

export interface Exposure extends Entity {
    type: string;
    internetFacing: string;
    attackSurface: string;
    relatedAssets: string;
    relatedFindings: string;
    mitigations: string;
    recommendation: Recommendation;
}
