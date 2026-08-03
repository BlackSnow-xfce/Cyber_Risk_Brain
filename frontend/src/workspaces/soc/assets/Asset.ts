import type { Entity } from "@/domain";
import type { Recommendation } from "@/recommendation";

export interface Asset extends Entity {
    type: string;
    owner: string;
    businessContext: string;
    relatedFindings: string;
    relatedInvestigations: string;
    vulnerabilities: string;
    recommendation: Recommendation;
}
