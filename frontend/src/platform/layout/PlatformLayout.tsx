import { Sidebar } from "../navigation/Sidebar";
import { Topbar } from "../navigation/Topbar";
import WorkspaceOutlet from "../workspace/WorkspaceOutlet";

export function PlatformLayout() {
    return (
        <div className="platform-layout">
            <Sidebar />

            <div className="platform-content">
                <Topbar />

                <main className="workspace-container">
                    <WorkspaceOutlet />
                </main>
            </div>
        </div>
    );
}