import type { RecommendationAction } from "./RecommendationAction";
import type { RecommendationPriority } from "./RecommendationPriority";
import type { RecommendationType } from "./RecommendationType";

export interface Recommendation {
    id: string;
    entityId: string;
    decisionId: string;
    type: RecommendationType;
    priority: RecommendationPriority;
    title: string;
    description: string;
    businessImpact: string;
    estimatedEffort: string;
    expectedRiskReduction: number;
    action: RecommendationAction;
}
