import type { Entity } from "@/domain";
import type { Recommendation } from "@/recommendation";

export interface Finding extends Entity {
    asset: string;
    recommendation: Recommendation;
}
