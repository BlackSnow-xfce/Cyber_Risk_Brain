import type { Workspace } from "@/types/workspace";
import { WorkspaceId } from "@/types/workspace";

export const workspaces: Workspace[] = [
    {
        id: WorkspaceId.DECISION_CENTER,
        name: "Decision Center",
        description:
            "AI-driven cyber decision making and explainability.",
        enabled: true,
    },
    {
        id: WorkspaceId.EXECUTIVE,
        name: "Executive",
        description:
            "Executive overview of enterprise cyber risk.",
        enabled: true,
    },
    {
        id: WorkspaceId.THREAT_HUNTING,
        name: "Threat Hunting",
        description:
            "Proactive threat hunting and attack path analysis.",
        enabled: false,
    },
    {
        id: WorkspaceId.INCIDENT_RESPONSE,
        name: "Incident Response",
        description:
            "Containment, eradication and recovery workflows.",
        enabled: false,
    },
    {
        id: WorkspaceId.RISK_MANAGEMENT,
        name: "Risk Management",
        description:
            "Business risk prioritization and governance.",
        enabled: false,
    },
    {
        id: WorkspaceId.ADMINISTRATION,
        name: "Administration",
        description:
            "Platform administration and integrations.",
        enabled: false,
    },
];
