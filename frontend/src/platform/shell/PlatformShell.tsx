import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function PlatformShell({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "grid",
                gridTemplateColumns: "280px 1fr",
                minHeight: "100vh",
                bgcolor: "background.default",
            }}
        >
            <aside />

            <Box
                component="main"
                sx={{
                    overflow: "auto",
                    p: 3,
                }}
            >
                {children}
            </Box>
        </Box>
    );
}