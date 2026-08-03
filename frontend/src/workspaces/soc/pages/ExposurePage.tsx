import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import ExposureWorkspace from "../exposure/ExposureWorkspace";

export default function ExposurePage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Exposure</Typography>

                <Typography color="text.secondary">
                    Review external exposure and attack surface context.
                </Typography>
            </Stack>

            <ExposureWorkspace />
        </Stack>
    );
}
