import DashboardWidget from "@/components/dashboard/DashboardWidget";

import Typography from "@mui/material/Typography";

export default function BusinessImpact() {
    return (
        <DashboardWidget
            title="Business Impact"
            subtitle="Operational business exposure"
            status="warning"
            statusLabel="Attention"
        >
            <Typography
                variant="h3"
                sx={{
                    fontWeight: 700,
                }}
            >
                High
            </Typography>

            <Typography
                sx={{
                    mt: 1,
                    color: "text.secondary",
                }}
            >
                Two critical business services are affected by the
                current attack path and require executive visibility.
            </Typography>
        </DashboardWidget>
    );
}