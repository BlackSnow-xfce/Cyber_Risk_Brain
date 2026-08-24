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

            <Panel component="section">
                <Typography variant="h6">
                    {isHuntsArea
                        ? "No hunts are available"
                        : "Workspace connection required"}
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    {isHuntsArea
                        ? "Connect a hunting data source before hunts can be shown here."
                        : "This workspace area is structurally available, but no hunting data source or execution capability is connected."}
                </Typography>
            </Panel>
        </Stack>
    );
}
