import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface IncidentResponseAreaPageProps {
    title: string;
    description: string;
}

export default function IncidentResponseAreaPage({
    title,
    description,
}: IncidentResponseAreaPageProps) {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="error.main">
                    Incident Response
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
                    Incident system connection required
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    This response area is structurally available, but no
                    incident data source or execution capability is connected.
                </Typography>
            </Panel>
        </Stack>
    );
}
