import Typography from "@mui/material/Typography";

import DecisionSection from "./DecisionSection";

export default function HighestPriorityDecision() {
    return (
        <DecisionSection title="Highest Priority Decision">
            <Typography
                variant="body2"
                color="text.secondary"
            >
                No active decision available.
            </Typography>
        </DecisionSection>
    );
}