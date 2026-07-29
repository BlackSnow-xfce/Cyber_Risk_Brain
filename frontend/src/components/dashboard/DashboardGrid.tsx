import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function DashboardGrid({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateColumns: "repeat(12, minmax(0, 1fr))",
                gap: 3,
                alignItems: "start",
                width: "100%",
            }}
        >
            {children}
        </Box>
    );
}