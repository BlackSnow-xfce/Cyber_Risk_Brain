import DashboardWidget from "@/components/dashboard/DashboardWidget";
import MetricRow from "@/components/dashboard/ui/MetricRow/MetricRow";

export default function RiskOverviewPanel() {
    return (
        <DashboardWidget
            title="Risk Overview"
            subtitle="Current enterprise posture"
            status="healthy"
            statusLabel="Healthy"
        >   

            <MetricRow
                label="Overall Risk Score"
                value="--"
            />

            <MetricRow
                label="Critical Risks"
                value="--"
            />

            <MetricRow
                label="Assets at Risk"
                value="--"
            />

            <MetricRow
                label="Active Decisions"
                value="--"
            />
        </DashboardWidget>
    );
}