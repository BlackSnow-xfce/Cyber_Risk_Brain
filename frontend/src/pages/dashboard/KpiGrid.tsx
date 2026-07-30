import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function KpiGrid({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateColumns:
                    "repeat(auto-fit, minmax(220px, 1fr))",
                gap: 2,
                width: "100%",
                marginBottom: 2,
            }}
        >
            {children}
        </Box>
    );
}