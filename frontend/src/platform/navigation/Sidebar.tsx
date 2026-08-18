import { ChevronsLeft } from "lucide-react";

import "./Sidebar.css";

import { useWorkspace } from "@/hooks/useWorkspace";
import { WorkspaceId } from "@/types/workspace";

import { getWorkspaceNavigation } from "@/workspaces";

import SidebarSection from "./SidebarSection";

export default function Sidebar() {
    const {
        workspace,
        activeNavigationItemId,
        setActiveNavigationItemId,
    } = useWorkspace();

    const navigation =
        getWorkspaceNavigation(workspace);
    const supportsWorkspaceFocus =
        workspace === WorkspaceId.DECISION_CENTER
        || workspace === WorkspaceId.THREAT_HUNTING
        || workspace === WorkspaceId.THREAT_INTELLIGENCE
        || workspace === WorkspaceId.INCIDENT_RESPONSE
        || workspace === WorkspaceId.RISK_MANAGEMENT
        || workspace === WorkspaceId.EXECUTIVE
        || workspace === WorkspaceId.ADMINISTRATION;
    const activeItemId = supportsWorkspaceFocus
        ? activeNavigationItemId ?? navigation[0]?.id
        : undefined;

    const sections = [
        ...new Set(
            navigation.map(
                (item) => item.section,
            ),
        ),
    ];

    return (
        <aside className="sidebar">
            <div className="sidebar-logo">
                <img
                    src="/logo.png"
                    alt="PredatorAI"
                    className="sidebar-logo-image"
                />

                <div className="sidebar-logo-text">
                    <div>PredatorAI</div>

                    <small>v3</small>
                </div>
            </div>

            {sections.map((section) => (
                <SidebarSection
                    key={section}
                    title={section}
                    items={navigation.filter(
                        (item) =>
                            item.section === section,
                    )}
                    activeItemId={activeItemId}
                    onSelect={
                        supportsWorkspaceFocus
                            ? setActiveNavigationItemId
                            : undefined
                    }
                />
            ))}

            <div className="sidebar-spacer" />

            <button className="sidebar-collapse">
                <ChevronsLeft size={18} />

                Collapse
            </button>
        </aside>
    );
}
