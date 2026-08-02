import type { PropsWithChildren } from "react";

import Box from "@mui/material/Box";

import Sidebar from "../navigation/Sidebar";
import Topbar from "../navigation/Topbar";

export default function PlatformLayout({
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
            <Sidebar />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateRows: "72px 1fr",
                    minHeight: "100vh",
                }}
            >
                <Topbar />

                <Box
                    component="main"
                    sx={{
                        p: 3,
                        overflow: "auto",
                    }}
                >
                    {children}
                </Box>
            </Box>
        </Box>
    );
}