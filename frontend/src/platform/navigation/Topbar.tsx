import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import {
    WorkspaceSwitcher,
    TimeRangeSelector,
    TopbarActions,
    UserMenu,
} from "@/components/topbar";

export default function Topbar() {
    return (
        <Stack
            direction="row"
            sx={{
                justifyContent: "space-between",
                alignItems: "center",
                height: 72,
                px: 3,
                borderBottom: 1,
                borderColor: "divider",
                bgcolor: "background.paper",
            }}
        >
            <Box>
                <Typography
                    variant="h5"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    Dashboard
                </Typography>

                <WorkspaceSwitcher />
            </Box>

            <Stack
                direction="row"
                spacing={2}
                sx={{
                    alignItems: "center",
                }}
            >
                <TimeRangeSelector />

                <TopbarActions />

                <UserMenu />
            </Stack>
        </Stack>
    );
}