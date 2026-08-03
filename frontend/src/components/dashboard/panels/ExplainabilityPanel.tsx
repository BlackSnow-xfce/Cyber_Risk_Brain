import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";

export default function ExplainabilityPanel() {
    return (
        <DashboardWidget
            title="Explainability"
            subtitle="Decision transparency"
            status="ready"
            statusLabel="Ready"
        >
            <Typography
                variant="body2"
                color="text.secondary"
            >
                Waiting for explainability data.
            </Typography>
        </DashboardWidget>
    );
}