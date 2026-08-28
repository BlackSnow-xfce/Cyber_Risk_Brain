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
                width: "100vw",
                height: "100vh",
                overflow: "hidden",
                bgcolor: "background.default",
            }}
        >
            <Sidebar />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateRows: "64px minmax(0, 1fr)",
                    minWidth: 0,
                    minHeight: 0,
                }}
            >
                <Topbar />

                <Box
                    component="main"
                    sx={{
                        minWidth: 0,
                        minHeight: 0,
                        p: 0,
                        overflowX: "auto",
                        overflowY: "auto",
                        bgcolor: "#010817",
                    }}
                >
                    {children}
                </Box>
            </Box>
        </Box>
    );
}
