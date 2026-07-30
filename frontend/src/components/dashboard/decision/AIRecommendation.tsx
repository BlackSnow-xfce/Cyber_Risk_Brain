import Typography from "@mui/material/Typography";

import DecisionSection from "./DecisionSection";

export default function AIRecommendation() {
    return (
        <DecisionSection title="AI Recommendation">
            <Typography
                variant="body2"
                color="text.secondary"
            >
                Waiting for Decision Engine...
            </Typography>
        </DecisionSection>
    );
}