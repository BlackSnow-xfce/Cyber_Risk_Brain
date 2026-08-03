import type { Entity } from "@/domain";

import type { Correlation } from "./Correlation";
import type { Evidence } from "./Evidence";

export interface ReasoningContext {
    entity: Entity;
    evidence: readonly Evidence[];
    correlations: readonly Correlation[];
}
