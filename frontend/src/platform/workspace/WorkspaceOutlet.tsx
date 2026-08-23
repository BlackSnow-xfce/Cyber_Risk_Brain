import { useEffect } from "react";

import { useWorkspace } from "@/hooks/useWorkspace";
import { useLocation } from "react-router-dom";

import { WorkspaceId } from "@/types/workspace";

import { AdministratorWorkspace } from "@/workspaces/administrator";
import { IncidentResponseWorkspace } from "@/workspaces/incident-response";
import { RiskManagerWorkspace } from "@/workspaces/risk-manager";
import { SOCWorkspace } from "@/workspaces/soc";
import { ExecutiveWorkspace } from "@/workspaces/executive";
import { ThreatHunterWorkspace } from "@/workspaces/threat-hunter";
import { ThreatIntelligenceWorkspace } from "@/workspaces/threat-intelligence";

export default function WorkspaceOutlet() {
    const { workspace, setWorkspace } = useWorkspace();
    const { pathname } = useLocation();

    const routeWorkspace = workspaceForPathname(pathname) ?? workspace;

    useEffect(() => {
        if (routeWorkspace !== workspace) {
            setWorkspace(routeWorkspace);
        }
    }, [routeWorkspace, setWorkspace, workspace]);

    if (/^\/incident-response\/incidents\/[^/]+\/command-center\/?$/.test(pathname)) {
        return <IncidentResponseWorkspace />;
    }

    switch (routeWorkspace) {
        case WorkspaceId.DECISION_CENTER:
            return <SOCWorkspace />;

        case WorkspaceId.EXECUTIVE:
            return <ExecutiveWorkspace />;

        case WorkspaceId.THREAT_HUNTING:
            return <ThreatHunterWorkspace />;

        case WorkspaceId.THREAT_INTELLIGENCE:
            return <ThreatIntelligenceWorkspace />;

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

function workspaceForPathname(pathname: string): WorkspaceId | null {
    if (/^\/incident-response(?:\/|$)/.test(pathname)) {
        return WorkspaceId.INCIDENT_RESPONSE;
    }
    if (/^\/threat-hunting(?:\/|$)/.test(pathname)) {
        return WorkspaceId.THREAT_HUNTING;
    }
    if (/^\/threat-intelligence(?:\/|$)/.test(pathname)) {
        return WorkspaceId.THREAT_INTELLIGENCE;
    }
    if (/^\/executive(?:\/|$)/.test(pathname)) {
        return WorkspaceId.EXECUTIVE;
    }
    if (/^\/risk-management(?:\/|$)/.test(pathname)) {
        return WorkspaceId.RISK_MANAGEMENT;
    }
    if (/^\/administration(?:\/|$)/.test(pathname)) {
        return WorkspaceId.ADMINISTRATION;
    }
    if (/^(?:\/$|\/(?:findings|investigations|assets|explainability|exposure)(?:\/|$))/.test(pathname)) {
        return WorkspaceId.DECISION_CENTER;
    }
    return null;
}
