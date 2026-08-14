import { useWorkspace } from "@/hooks/useWorkspace";

import { WorkspaceId } from "@/types/workspace";

import { AdministratorWorkspace } from "@/workspaces/administrator";
import { IncidentResponseWorkspace } from "@/workspaces/incident-response";
import { RiskManagerWorkspace } from "@/workspaces/risk-manager";
import { SOCWorkspace } from "@/workspaces/soc";
import { ExecutiveWorkspace } from "@/workspaces/executive";
import { ThreatHunterWorkspace } from "@/workspaces/threat-hunter";

export default function WorkspaceOutlet() {
    const { workspace } = useWorkspace();

    switch (workspace) {
        case WorkspaceId.DECISION_CENTER:
            return <SOCWorkspace />;

        case WorkspaceId.EXECUTIVE:
            return <ExecutiveWorkspace />;

        case WorkspaceId.THREAT_HUNTING:
            return <ThreatHunterWorkspace />;

        case WorkspaceId.INCIDENT_RESPONSE:
            return <IncidentResponseWorkspace />;

        case WorkspaceId.RISK_MANAGEMENT:
            return <RiskManagerWorkspace />;

        case WorkspaceId.ADMINISTRATION:
            return <AdministratorWorkspace />;

        default:
            return <SOCWorkspace />;
    }
}
