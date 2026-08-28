import { ChevronsLeft, ChevronsUpDown } from "lucide-react";

import "./Sidebar.css";

import { useWorkspace } from "@/hooks/useWorkspace";
import { WorkspaceId } from "@/types/workspace";
import { useLocation, useNavigate } from "react-router-dom";

import { getWorkspaceNavigation, workspaceRegistry } from "@/workspaces";

import SidebarSection from "./SidebarSection";

export default function Sidebar() {
    const {
        workspace,
        activeNavigationItemId,
        setActiveNavigationItemId,
    } = useWorkspace();
    const { pathname, search } = useLocation();
    const navigate = useNavigate();

    const navigation =
        getWorkspaceNavigation(workspace);
    const workspaceName = workspaceRegistry.find((item) => item.id === workspace)?.name
        ?? "Unavailable";
    const supportsWorkspaceFocus =
        workspace === WorkspaceId.DECISION_CENTER
        || workspace === WorkspaceId.THREAT_HUNTING
        || workspace === WorkspaceId.THREAT_INTELLIGENCE
        || workspace === WorkspaceId.INCIDENT_RESPONSE
        || workspace === WorkspaceId.RISK_MANAGEMENT
        || workspace === WorkspaceId.EXECUTIVE
        || workspace === WorkspaceId.ADMINISTRATION;
    const activeRouteItem = navigation.find((item) =>
        matchesNavigationRoute(item.route, pathname),
    );
    const isIncidentCommandCenterPath =
        /^\/incident-response\/incidents\/[^/]+\/command-center\/?$/.test(
            pathname,
        );
    const activeItemId = supportsWorkspaceFocus
        ? activeRouteItem?.id
            ?? (isIncidentCommandCenterPath
                ? undefined
                : activeNavigationItemId ?? undefined)
        : undefined;

    const handleSelect = (itemId: string) => {
        const item = navigation.find((candidate) => candidate.id === itemId);
        if (!item) {
            return;
        }

        setActiveNavigationItemId(item.id);
        if (item.route.includes(":incidentId")) {
            return;
        }

        const findingId = pathname === "/findings"
            ? new URLSearchParams(search).get("findingId")
            : null;
        const route = item.route === "/" && findingId
            ? `/?findingId=${encodeURIComponent(findingId)}`
            : item.route;
        navigate(route);
    };

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
                            ? handleSelect
                            : undefined
                    }
                />
            ))}

            <div className="sidebar-spacer" />

            <button className="sidebar-collapse">
                <ChevronsLeft size={12} />

                Collapse
            </button>

            <div className="sidebar-workspace" aria-label={`Current workspace: ${workspaceName}`}>
                <span className="sidebar-workspace-mark">EA</span>
                <span><strong>{workspaceName}</strong><small>Current workspace</small></span>
                <ChevronsUpDown size={11} aria-hidden="true" />
            </div>

            <small className="sidebar-version">PREDATORAI v3.0.0</small>
        </aside>
    );
}

function matchesNavigationRoute(route: string, pathname: string): boolean {
    const pattern = route
        .split("/")
        .map((segment) =>
            segment.startsWith(":") ? "[^/]+" : escapeRegExp(segment),
        )
        .join("/");

    return new RegExp(`^${pattern}/?$`).test(pathname);
}

function escapeRegExp(value: string): string {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
