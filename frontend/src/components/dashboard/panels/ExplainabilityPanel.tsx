import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function ExplainabilityPanel() {
    return (
        <DashboardWidget
            title="Explainability"
            subtitle="Decision transparency"
            status="ready"
            statusLabel="Ready"
        >
            <p>Waiting for explainability data.</p>
        </DashboardWidget>
    );
}