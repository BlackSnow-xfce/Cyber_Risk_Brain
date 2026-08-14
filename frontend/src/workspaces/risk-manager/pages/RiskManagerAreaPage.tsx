import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface RiskManagerAreaPageProps {
    title: string;
    description: string;
}

export default function RiskManagerAreaPage({
    title,
    description,
}: RiskManagerAreaPageProps) {
    return (
        <Stack spacing={3}>
            <Box component="header">
                <Typography variant="overline" color="info.main">
                    Risk Manager
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
                    Enterprise risk source required
                </Typography>

                <Typography color="text.secondary" sx={{ mt: 1 }}>
                    This governance area is structurally available, but no
                    authorized risk or business data source is connected.
                </Typography>
            </Panel>
        </Stack>
    );
}
