import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface AdministratorAreaPageProps {
    title: string;
    description: string;
}

export default function AdministratorAreaPage({
    title,
    description,
}: AdministratorAreaPageProps) {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="text.secondary">
                    Administrator
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
                    Platform source required
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    This administration area is structurally available, but no
                    authorized platform source or operation is connected.
                </Typography>
            </Panel>
        </Stack>
    );
}
