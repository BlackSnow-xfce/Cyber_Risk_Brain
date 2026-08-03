import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import AssetsWorkspace from "../assets/AssetsWorkspace";

export default function AssetsPage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Assets</Typography>

                <Typography color="text.secondary">
                    Review assets and their security context.
                </Typography>
            </Stack>

            <AssetsWorkspace />
        </Stack>
    );
}
