import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import InvestigationsWorkspace from "../investigations/InvestigationsWorkspace";

export default function InvestigationsPage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">Investigations</Typography>

                <Typography color="text.secondary">
                    Coordinate and review active security investigations.
                </Typography>
            </Stack>

            <InvestigationsWorkspace />
        </Stack>
    );
}
