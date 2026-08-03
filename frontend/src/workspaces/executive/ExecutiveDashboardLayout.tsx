import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function ExecutiveDashboardLayout({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateColumns: {
                    xs: "1fr",
                    xl: "repeat(2, 1fr)",
                },
                gap: 3,
                alignItems: "start",
            }}
        >
            {children}
        </Box>
    );
}