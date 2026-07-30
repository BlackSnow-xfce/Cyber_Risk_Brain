import DashboardWidget from "@/components/dashboard/DashboardWidget";

import DecisionWorkspace from "@/components/dashboard/decision/DecisionWorkspace";

import { mockDecision } from "@/mocks/mockDecision";

export default function DecisionCenterPanel() {
    return (
        <DashboardWidget
            title="Decision Workspace"
            subtitle="Explainable AI-driven cyber decisions"
            status="live"
            statusLabel="Decision Engine"
        >
            <DecisionWorkspace
                decision={mockDecision}
            />
        </DashboardWidget>
    );
}