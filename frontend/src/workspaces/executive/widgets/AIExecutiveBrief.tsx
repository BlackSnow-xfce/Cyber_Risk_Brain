import DashboardWidget from "@/components/dashboard/DashboardWidget";

import Typography from "@mui/material/Typography";

export default function AIExecutiveBrief() {
    return (
        <DashboardWidget
            title="AI Executive Brief"
            subtitle="Strategic situation assessment"
            status="live"
            statusLabel="Reasoning"
        >
            <Typography>
                PredatorAI currently assesses the enterprise cyber risk
                as elevated. One critical decision requires executive
                attention due to the potential impact on business
                operations.
            </Typography>

            <Typography sx={{ mt: 2 }}>
                Recommended priority:
            </Typography>

            <Typography sx={{ mt: 1 }}>
                • Reduce exposure of internet-facing assets.
            </Typography>

            <Typography>
                • Prioritize remediation of critical attack paths.
            </Typography>

            <Typography>
                • Review business services affected by the current risk.
            </Typography>
        </DashboardWidget>
    );
}