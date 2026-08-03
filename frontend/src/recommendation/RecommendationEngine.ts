import type { Recommendation } from "./Recommendation";
import type { RecommendationContext } from "./RecommendationContext";

export interface RecommendationEngine {
    recommend: (
        context: RecommendationContext,
    ) => Promise<Recommendation>;
}
