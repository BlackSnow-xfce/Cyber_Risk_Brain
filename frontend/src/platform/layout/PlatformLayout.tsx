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
                gridTemplateColumns: "164px minmax(0, 1fr)",
                minHeight: "100vh",
                bgcolor: "background.default",
            }}
        >
            <Sidebar />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateRows: "64px minmax(0, 1fr)",
                    minHeight: "100vh",
                }}
            >
                <Topbar />

                <Box
                    component="main"
                    sx={{
                        p: 0,
                        overflow: "auto",
                        bgcolor: "#010817",
                    }}
                >
                    {children}
                </Box>
            </Box>
        </Box>
    );
}
