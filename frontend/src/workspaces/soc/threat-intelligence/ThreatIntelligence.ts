import type { Entity } from "@/domain";
import type { Recommendation } from "@/recommendation";

export interface ThreatIntelligence extends Entity {
    type: string;
    source: string;
    lastUpdated: string;
    intelligenceSource: string;
    indicators: string;
    relatedAssets: string;
    recommendation: Recommendation;
}
