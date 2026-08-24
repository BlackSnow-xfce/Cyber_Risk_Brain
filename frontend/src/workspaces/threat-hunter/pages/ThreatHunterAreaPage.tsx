import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface ThreatHunterAreaPageProps {
    title: string;
    description: string;
}

export default function ThreatHunterAreaPage({
    title,
    description,
}: ThreatHunterAreaPageProps) {
    const isHuntsArea = title === "Hunts";

    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="warning.main">
                    Threat Hunter
                </Typography>

                <Typography variant="h4" sx={{ fontWeight: 700 }}>
                    {title}
                </Typography>

                <Typography
                    color="text.secondary"
                    sx={{ mt: 1, maxWidth: 720 }}
                >
                    {description}
                </Typography>
            </Box>

            {isHuntsArea ? (
                <Alert severity="info">
                    <Typography variant="h6">No hunts are available</Typography>
                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                        Connect a hunting data source to make hunts available here.
                    </Typography>
                </Alert>
            ) : (
                <Panel component="section">
                    <Typography variant="h6">
                        Workspace connection required
                    </Typography>

                    <Typography color="text.secondary" sx={{ mt: 1 }}>
                        This workspace area is structurally available, but no
                        hunting data source or execution capability is connected.
                    </Typography>
                </Panel>
            )}
        </Stack>
    );
}
