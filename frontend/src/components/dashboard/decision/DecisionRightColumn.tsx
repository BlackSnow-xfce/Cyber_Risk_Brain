import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "./DecisionSection";

export default function DecisionRightColumn() {
    return (
        <Stack spacing={3}>
            <DecisionSection title="Explainability">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    No reasoning available.
                </Typography>
            </DecisionSection>

            <DecisionSection title="Evidence">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    No evidence available.
                </Typography>
            </DecisionSection>

            <DecisionSection title="Confidence">
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Confidence has not yet been calculated.
                </Typography>
            </DecisionSection>
        </Stack>
    );
}