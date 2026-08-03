import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import FindingsWorkspace from "../findings/FindingsWorkspace";

export default function FindingsPage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Findings</Typography>

                <Typography color="text.secondary">
                    Review, prioritize and investigate security findings.
                </Typography>
            </Stack>

            <FindingsWorkspace />
        </Stack>
    );
}
