import { WorkspaceId } from "@/types/workspace";

import { administratorNavigation } from "../administrator/navigation";
import { incidentResponseNavigation } from "../incident-response/navigation";
import { riskManagerNavigation } from "../risk-manager/navigation";
import { socNavigation } from "../soc/navigation";
import { executiveNavigation } from "../executive/navigation";
import { threatHunterNavigation } from "../threat-hunter/navigation";
import { threatIntelligenceNavigation } from "../threat-intelligence/navigation";

export function getWorkspaceNavigation(
    workspace: WorkspaceId,
) {
    switch (workspace) {
        case WorkspaceId.DECISION_CENTER:
            return socNavigation;

        case WorkspaceId.EXECUTIVE:
            return executiveNavigation;

        case WorkspaceId.THREAT_HUNTING:
            return threatHunterNavigation;

        case WorkspaceId.THREAT_INTELLIGENCE:
            return threatIntelligenceNavigation;

        case WorkspaceId.INCIDENT_RESPONSE:
            return incidentResponseNavigation;

        case WorkspaceId.RISK_MANAGEMENT:
            return riskManagerNavigation;

        case WorkspaceId.ADMINISTRATION:
            return administratorNavigation;

        default:
            return socNavigation;
    }
}
