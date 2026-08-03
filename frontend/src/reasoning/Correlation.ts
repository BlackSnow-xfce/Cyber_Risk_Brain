import type { CorrelationStrength } from "./CorrelationStrength";
import type { CorrelationType } from "./CorrelationType";

export type CorrelationTargetType =
    | "Finding"
    | "Asset"
    | "Investigation"
    | "ThreatIntelligence"
    | "Exposure";

export interface Correlation {
    id: string;
    type: CorrelationType;
    targetType: CorrelationTargetType;
    targetId: string;
    title: string;
    description: string;
    strength: CorrelationStrength;
    confidence: number;
}
