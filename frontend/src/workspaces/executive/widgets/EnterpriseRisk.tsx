import DashboardWidget from "@/components/dashboard/DashboardWidget";

import Typography from "@mui/material/Typography";

export default function EnterpriseRisk() {
    return (
        <DashboardWidget
            title="Enterprise Risk"
            subtitle="Current business exposure"
            status="warning"
            statusLabel="Elevated"
        >
            <Typography variant="h3">
                82
            </Typography>

            <Typography
                sx={{
                    mt: 1,
                    color: "text.secondary",
                }}
            >
                Overall enterprise cyber risk score.
            </Typography>
        </DashboardWidget>
    );
}