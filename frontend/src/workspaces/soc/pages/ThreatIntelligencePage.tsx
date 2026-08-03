import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import ThreatIntelligenceWorkspace from "../threat-intelligence/ThreatIntelligenceWorkspace";

export default function ThreatIntelligencePage() {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography variant="h4">
                    Threat Intelligence
                </Typography>

                <Typography color="text.secondary">
                    Review threat intelligence and its security context.
                </Typography>
            </Stack>

            <ThreatIntelligenceWorkspace />
        </Stack>
    );
}
