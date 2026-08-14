import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface ExecutiveAreaPageProps {
    title: string;
    description: string;
}

export default function ExecutiveAreaPage({
    title,
    description,
}: ExecutiveAreaPageProps) {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="warning.main">
                    Executive
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
                    Strategic data source required
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    This executive area is structurally available, but no
                    authorized enterprise or reporting source is connected.
                </Typography>
            </Panel>
        </Stack>
    );
}
