import { Fragment, useState } from "react";
import { Check, ChevronDown } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useWorkspace } from "@/hooks/useWorkspace";
import { WorkspaceId } from "@/types/workspace";
import { workspaceRegistry } from "@/workspaces";

const workspaceRoutes: Record<WorkspaceId, string> = {
    [WorkspaceId.DECISION_CENTER]: "/",
    [WorkspaceId.THREAT_HUNTING]: "/threat-hunting",
    [WorkspaceId.THREAT_INTELLIGENCE]: "/threat-intelligence",
    [WorkspaceId.INCIDENT_RESPONSE]: "/incident-response",
    [WorkspaceId.EXECUTIVE]: "/executive",
    [WorkspaceId.RISK_MANAGEMENT]: "/risk-management",
    [WorkspaceId.ADMINISTRATION]: "/administration",
};

interface WorkspaceGroup {
    label: string;
    workspaceIds: WorkspaceId[];
}

const workspaceGroups: WorkspaceGroup[] = [
    {
        label: "SOC WORKSPACES",
        workspaceIds: [
            WorkspaceId.DECISION_CENTER,
            WorkspaceId.THREAT_HUNTING,
            WorkspaceId.THREAT_INTELLIGENCE,
            WorkspaceId.INCIDENT_RESPONSE,
        ],
    },
    {
        label: "MANAGEMENT WORKSPACES",
        workspaceIds: [
            WorkspaceId.EXECUTIVE,
            WorkspaceId.RISK_MANAGEMENT,
        ],
    },
    {
        label: "SYSTEM / ADMINISTRATION",
        workspaceIds: [WorkspaceId.ADMINISTRATION],
    },
];

export default function WorkspaceSwitcher() {
    const { workspace, setWorkspace } = useWorkspace();
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    const currentWorkspace = workspaceRegistry.find((item) => item.id === workspace);
    return <span className="workspace-switcher">
        <button type="button" aria-haspopup="menu" aria-expanded={open} aria-label={`Change workspace, current workspace ${currentWorkspace?.name ?? "Unavailable"}`} onClick={() => setOpen((value) => !value)}>{currentWorkspace?.name ?? "Workspace unavailable"} <ChevronDown size={9} /></button>
        {open && <span className="workspace-menu" role="menu">{workspaceGroups.map((group, groupIndex) => {
            const labelId = `workspace-group-${groupIndex}`;
            return <Fragment key={group.label}>
                {groupIndex > 0 && <span className="workspace-menu-divider" role="separator" />}
                <span className="workspace-menu-group" role="group" aria-labelledby={labelId}>
                    <span className="workspace-menu-label" id={labelId}>{group.label}</span>
                    {group.workspaceIds.map((workspaceId) => workspaceRegistry.find((item) => item.id === workspaceId)).filter((item) => item?.enabled).map((item) => item && <button key={item.id} type="button" role="menuitem" aria-current={workspace === item.id ? "true" : undefined} onClick={() => { setWorkspace(item.id); navigate(workspaceRoutes[item.id]); setOpen(false); }}><span>{item.name}</span>{workspace === item.id && <Check className="workspace-menu-check" aria-label="Selected" />}</button>)}
                </span>
            </Fragment>;
        })}</span>}
    </span>;
}
