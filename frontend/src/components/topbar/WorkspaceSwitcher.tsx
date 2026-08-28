import { useState } from "react";
import { ChevronDown } from "lucide-react";
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

export default function WorkspaceSwitcher() {
    const { workspace, setWorkspace } = useWorkspace();
    const navigate = useNavigate();
    const [open, setOpen] = useState(false);
    return <span className="workspace-switcher">
        <button type="button" aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((value) => !value)}>Enterprise Workspace <ChevronDown size={9} /></button>
        {open && <span className="workspace-menu" role="menu">{workspaceRegistry.filter(({ enabled }) => enabled).map((item) => <button key={item.id} type="button" role="menuitem" aria-current={workspace === item.id ? "true" : undefined} onClick={() => { setWorkspace(item.id); navigate(workspaceRoutes[item.id]); setOpen(false); }}>{item.name}</button>)}</span>}
    </span>;
}
