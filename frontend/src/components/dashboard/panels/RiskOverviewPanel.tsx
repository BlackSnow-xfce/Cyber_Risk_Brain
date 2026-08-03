import DashboardWidget from "@/components/dashboard/DashboardWidget";
import MetricRow from "@/components/dashboard/ui/MetricRow/MetricRow";

export default function RiskOverviewPanel() {
    const metrics = [
        {
            label: "Overall Risk Score",
            value: "--",
        },
        {
            label: "Critical Risks",
            value: "--",
        },
        {
            label: "Assets at Risk",
            value: "--",
        },
        {
            label: "Active Decisions",
            value: "--",
        },
    ];

    return (
        <DashboardWidget
            title="Risk Overview"
            subtitle="Current enterprise posture"
            status="healthy"
            statusLabel="Healthy"
        >
            {metrics.map((metric) => (
                <MetricRow
                    key={metric.label}
                    label={metric.label}
                    value={metric.value}
                />
            ))}
        </DashboardWidget>
    );
}