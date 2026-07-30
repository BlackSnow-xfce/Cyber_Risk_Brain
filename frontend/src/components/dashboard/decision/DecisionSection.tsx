import type { ReactNode } from "react";

import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface DecisionSectionProps {
    title: string;
    children: ReactNode;
}

export default function DecisionSection({
    title,
    children,
}: DecisionSectionProps) {
    return (
        <Box
            sx={{
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
                p: 2.5,
                height: "100%",
            }}
        >
            <Stack spacing={2}>
                <Typography
                    variant="subtitle1"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    {title}
                </Typography>

                {children}
            </Stack>
        </Box>
    );
}