import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function TimelinePanel() {
    return (
        <DashboardWidget
            title="Timeline"
            subtitle="Recent platform activity"
            status="offline"
            statusLabel="Idle"
        >
            <p>No events available.</p>
        </DashboardWidget>
    );
}