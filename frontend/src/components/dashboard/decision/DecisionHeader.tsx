import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import StatusBadge from "@/ui/badge/StatusBadge";

export default function DecisionHeader() {
    return (
        <Stack
            direction="row"
            sx={{
                justifyContent: "space-between",
                alignItems: "center",
            }}
        >
            <Box>
                <Typography
                    component="h2"
                    variant="h5"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    Decision Workspace
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Explainable AI-driven cyber decisions
                </Typography>
            </Box>

            <StatusBadge
                status="info"
                label="Waiting"
            />
        </Stack>
    );
}