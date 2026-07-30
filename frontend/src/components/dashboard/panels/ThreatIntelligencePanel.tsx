import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function ThreatIntelligencePanel() {
    return (
        <DashboardWidget
            title="Threat Intelligence"
            subtitle="External intelligence feeds"
            status="live"
            statusLabel="Live"
        >
            <p>No threat intelligence available.</p>
        </DashboardWidget>
    );
}