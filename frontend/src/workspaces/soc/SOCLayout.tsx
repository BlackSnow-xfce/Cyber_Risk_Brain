import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

export default function SOCLayout({
    children,
}: PropsWithChildren) {
    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
                width: "100%",
            }}
        >
            {children}
        </Box>
    );
}