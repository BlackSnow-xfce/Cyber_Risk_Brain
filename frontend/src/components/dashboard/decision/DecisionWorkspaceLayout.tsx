import type { ReactNode } from "react";

import Box from "@mui/material/Box";

interface DecisionWorkspaceLayoutProps {
    left: ReactNode;
    right: ReactNode;
    bottom?: ReactNode;
}

export default function DecisionWorkspaceLayout({
    left,
    right,
    bottom,
}: DecisionWorkspaceLayoutProps) {
    return (
        <Box
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,
            }}
        >
            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "1fr",
                        lg: "1.4fr 1fr",
                    },
                    gap: 3,
                }}
            >
                {left}
                {right}
            </Box>

            {bottom}
        </Box>
    );
}