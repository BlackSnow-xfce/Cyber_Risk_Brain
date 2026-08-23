import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

interface IntelligenceStateCardProps {
    title: string;
    description: string;
    status: string;
}

export default function IntelligenceStateCard({
    title,
    description,
    status,
}: IntelligenceStateCardProps) {
    return (
        <Panel component="section" sx={{ minHeight: 156 }}>
            <Stack spacing={1.5}>
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: "flex-start", justifyContent: "space-between" }}
                >
                    <Typography variant="h6">{title}</Typography>
                    <Chip label={status} size="small" variant="outlined" />
                </Stack>
                <Typography variant="body2" color="text.secondary">
                    {description}
                </Typography>
            </Stack>
        </Panel>
    );
}
