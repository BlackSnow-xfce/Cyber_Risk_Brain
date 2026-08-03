import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function TimelinePanel() {
    return (
        <DashboardWidget
            title="Timeline"
            subtitle="Recent platform activity"
            status="offline"
            statusLabel="Idle"
        >
            <Typography
                variant="body2"
                color="text.secondary"
            >
                No events available.
            </Typography>
        </DashboardWidget>
    );
}