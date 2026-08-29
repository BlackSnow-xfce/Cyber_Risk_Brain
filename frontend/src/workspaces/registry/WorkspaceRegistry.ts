import type { Workspace } from "@/types/workspace";
import { WorkspaceId } from "@/types/workspace";

export const workspaceRegistry: Workspace[] = [
    {
        id: WorkspaceId.DECISION_CENTER,
        name: "SOC Analyst",
        description: "Security Operations Center",
        order: 1,
        enabled: true,
    },
    {
        id: WorkspaceId.THREAT_HUNTING,
        name: "Threat Hunter",
        description: "Proactive Threat Hunting",
        order: 2,
        enabled: true,
    },
    {
        id: WorkspaceId.THREAT_INTELLIGENCE,
        name: "Threat Intelligence",
        description: "Intelligence & Environment Context",
        order: 3,
        enabled: true,
    },
    {
        id: WorkspaceId.INCIDENT_RESPONSE,
        name: "Incident Response",
        description: "Containment & Recovery",
        order: 4,
        enabled: true,
    },
    {
        id: WorkspaceId.EXECUTIVE,
        name: "CISO / ISO",
        description: "Board & Business Overview",
        order: 5,
        enabled: true,
    },
    {
        id: WorkspaceId.RISK_MANAGEMENT,
        name: "Risk Manager",
        description: "Business Risk & Governance",
        order: 6,
        enabled: true,
    },
    {
        id: WorkspaceId.ADMINISTRATION,
        name: "Administrator",
        description: "Platform Configuration",
        order: 7,
        enabled: true,
    },
];
