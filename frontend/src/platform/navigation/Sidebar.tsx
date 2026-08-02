import { ChevronsLeft } from "lucide-react";

import "./Sidebar.css";

import { useWorkspace } from "@/hooks/useWorkspace";

import { getWorkspaceNavigation } from "@/workspaces";

import SidebarSection from "./SidebarSection";

export default function Sidebar() {
    const { workspace } = useWorkspace();

    const navigation =
        getWorkspaceNavigation(workspace);

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