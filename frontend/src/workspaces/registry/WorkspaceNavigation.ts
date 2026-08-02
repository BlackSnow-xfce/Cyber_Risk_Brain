import { WorkspaceId } from "@/types/workspace";

import { socNavigation } from "../soc/navigation";
import { executiveNavigation } from "../executive/navigation";

export function getWorkspaceNavigation(
    workspace: WorkspaceId,
) {
    switch (workspace) {
        case WorkspaceId.DECISION_CENTER:
            return socNavigation;

        case WorkspaceId.EXECUTIVE:
            return executiveNavigation;

        case WorkspaceId.THREAT_HUNTING:
            return [];

        case WorkspaceId.RISK_MANAGEMENT:
            return [];

        case WorkspaceId.ADMINISTRATION:
            return [];

        default:
            return socNavigation;
    }
}