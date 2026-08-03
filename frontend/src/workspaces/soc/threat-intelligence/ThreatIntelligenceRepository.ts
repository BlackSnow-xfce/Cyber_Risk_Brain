import type { ThreatIntelligence } from "./ThreatIntelligence";

export interface ThreatIntelligenceRepository {
    getThreatIntelligence: () => readonly ThreatIntelligence[];
}
