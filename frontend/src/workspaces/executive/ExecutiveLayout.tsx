import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function ExecutiveLayout({
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
                p: 3,
                boxSizing: "border-box",
            }}
        >
            {children}
        </Box>
    );
}
