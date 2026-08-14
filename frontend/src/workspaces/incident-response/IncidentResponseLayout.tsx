import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function IncidentResponseLayout({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
                width: "100%",
                minWidth: 0,
            }}
        >
            {children}
        </Box>
    );
}
