import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function ThreatIntelligencePanel() {
    return (
        <DashboardWidget
            title="Threat Intelligence"
            subtitle="External intelligence feeds"
            status="live"
            statusLabel="Live"
        >
            <Typography
                variant="body2"
                color="text.secondary"
            >
                No threat intelligence available.
            </Typography>
        </DashboardWidget>
    );
}