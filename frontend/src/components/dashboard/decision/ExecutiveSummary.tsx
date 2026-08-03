import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";

import type { Decision } from "@/types/decision";

interface ExecutiveSummaryProps {
    decision: Decision;
}

export default function ExecutiveSummary({
    decision,
}: ExecutiveSummaryProps) {
    return (
        <DecisionSection
            title="Executive Summary"
            subtitle={decision.summary.subtitle}
        >
            <Stack spacing={2}>
                <Typography
                    variant="body1"
                    color="text.secondary"
                    sx={{
                        lineHeight: 1.8,
                    }}
                >
                    {decision.summary.description}
                </Typography>
            </Stack>
        </DecisionSection>
    );
}