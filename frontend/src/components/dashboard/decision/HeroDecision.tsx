import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import ConfidenceBar from "@/components/dashboard/ui/ConfidenceBar/ConfidenceBar";

import type { DecisionResponse } from "@/types/decision/DecisionResponse";

interface HeroDecisionProps {
    decision: DecisionResponse;
}

export default function HeroDecision({
    decision,
}: HeroDecisionProps) {
    return (
        <DashboardWidget
            title="Decision"
            subtitle="Highest priority AI-driven decision"
            status="offline"
            statusLabel={decision.status.toUpperCase()}
        >
            <Stack spacing={3}>

                <Stack spacing={1}>
                    <Typography
                        variant="h5"
                        sx={{ fontWeight: 700 }}
                    >
                        {decision.decision.title}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {decision.decision.description}
                    </Typography>
                </Stack>

                <ConfidenceBar
                    value={decision.confidence}
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