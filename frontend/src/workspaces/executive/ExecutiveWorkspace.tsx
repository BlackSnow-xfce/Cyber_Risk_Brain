import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

import ExecutiveLayout from "./ExecutiveLayout";

export default function ExecutiveWorkspace() {
    return (
        <ExecutiveLayout>
            <Box>
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    Executive Workspace
                </Typography>

                <Typography
                    sx={{
                        mt: 1,
                        color: "text.secondary",
                    }}
                >
                    AI-driven executive decision support for cyber risk,
                    business impact and strategic security posture.
                </Typography>
            </Box>
        </ExecutiveLayout>
    );
}