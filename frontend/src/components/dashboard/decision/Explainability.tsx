import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";
import ReasoningStep from "@/components/dashboard/ui/ReasoningStep";

import type { Decision } from "@/types/decision";

interface ExplainabilityProps {
    decision: Decision;
}

export default function Explainability({
    decision,
}: ExplainabilityProps) {
    return (
        <DecisionSection
            title="AI Context"
            subtitle="Decision Explainability"
        >
            <Stack spacing={3}>
                <Stack spacing={0.5}>
                    <Typography
                        variant="h2"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {decision.confidence.score}%
                    </Typography>

                    <Typography
                        variant="subtitle1"
                        color="primary"
                    >
                        Decision Confidence
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        Overall confidence based on correlated
                        technical and business evidence.
                    </Typography>
                </Stack>

                <Divider />

                <Stack spacing={2}>
                    <Typography variant="h6">
                        Reasoning
                    </Typography>

                    <ReasoningStep
                        step={1}
                        title="Decision Engine"
                        description={
                            decision.explainability.reasoning
                        }
                    />
                </Stack>

                <Divider />

                <Stack spacing={1}>
                    <Typography variant="h6">
                        Decision Metadata
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        Engine: {decision.metadata.engineVersion}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        Model: {decision.metadata.modelVersion}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        Status: {decision.status.state}
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        Confidence Level: {decision.confidence.level}
                    </Typography>
                </Stack>
            </Stack>
        </DecisionSection>
    );
}