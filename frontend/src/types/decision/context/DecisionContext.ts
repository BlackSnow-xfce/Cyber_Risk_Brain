import type { AssetContext } from "./AssetContext";
import type { BusinessContext } from "./BusinessContext";
import type { ThreatContext } from "./ThreatContext";

export interface DecisionContext {
    asset: AssetContext;

    threat: ThreatContext;

    business: BusinessContext;
}