import Alert from "@mui/material/Alert";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export default function ExplainabilityWorkspace() {
    return (
        <Stack spacing={2}>
            <Alert severity="info" aria-label="Explainability unavailable">
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
                    Explainability context is unavailable
                </Typography>
                <Typography variant="body2">
                    No authoritative explainability context is available for this
                    view. PredatorAI will not generate or infer an explanation
                    without grounded finding, evidence, and reasoning data.
                </Typography>
            </Alert>
        </Stack>
    );
}
