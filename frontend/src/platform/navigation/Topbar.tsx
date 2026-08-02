import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

import {
    WorkspaceSelector,
    TimeRangeSelector,
    TopbarActions,
    UserMenu,
} from "@/components/topbar";

import "./Topbar.css";

export function Topbar() {
    return (
        <header className="topbar">
            <Box
                className="topbar-left"
                sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 3,
                }}
            >
                <Typography
                    variant="h4"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    Dashboard
                </Typography>

                <WorkspaceSelector />
            </Box>

            <Box
                className="topbar-right"
                sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 2,
                }}
            >
                <TimeRangeSelector />

                <TopbarActions />

                <UserMenu />
            </Box>
        </header>
    );
}