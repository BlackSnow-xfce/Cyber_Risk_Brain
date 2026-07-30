import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "./DecisionSection";

export default function DecisionLeftColumn() {
    return (
        <Stack spacing={3}>
            <DecisionSection title="Highest Priority Decision">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    No active decision available.
                </Typography>
            </DecisionSection>

            <DecisionSection title="AI Recommendation">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Waiting for Decision Engine...
                </Typography>
            </DecisionSection>

            <DecisionSection title="Business Impact">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    No business context available.
                </Typography>
            </DecisionSection>
        </Stack>
    );
}