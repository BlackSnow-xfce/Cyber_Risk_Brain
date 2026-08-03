import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import ExplainabilityWorkspace from "../explainability/ExplainabilityWorkspace";

export default function ExplainabilityPage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Explainability</Typography>
                <Typography color="text.secondary">
                    Analyze the complete cyber-reasoning decision chain.
                </Typography>
            </Stack>
            <ExplainabilityWorkspace />
        </Stack>
    );
}
