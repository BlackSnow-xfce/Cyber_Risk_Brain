import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import ConfidenceBar from "@/components/dashboard/ui/ConfidenceBar/ConfidenceBar";

import type { Decision } from "@/types/decision";

interface HeroDecisionProps {
    decision: Decision;
}

export default function HeroDecision({
    decision,
}: HeroDecisionProps) {
    return (
        <DashboardWidget
            title="Decision"
            subtitle="Highest priority AI-driven decision"
            status="offline"
            statusLabel={decision.status.state.toUpperCase()}
        >
            <Stack spacing={3}>
                <Stack spacing={1}>
                    <Typography
                        variant="h5"
                        sx={{ fontWeight: 700 }}
                    >
                        {decision.summary.title}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {decision.summary.description}
                    </Typography>
                </Stack>

                <ConfidenceBar
                    value={decision.confidence.score}
                />

                <Stack
                    direction="row"
                    spacing={2}
                >
                    <Button variant="contained">
                        Open Decision
                    </Button>

                    <Button variant="outlined">
                        Refresh
                    </Button>
                </Stack>
            </Stack>
        </DashboardWidget>
    );
}