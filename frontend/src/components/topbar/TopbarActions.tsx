import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import DarkModeRoundedIcon from "@mui/icons-material/DarkModeRounded";
import NotificationsNoneRoundedIcon from "@mui/icons-material/NotificationsNoneRounded";
import SearchRoundedIcon from "@mui/icons-material/SearchRounded";
import ShareRoundedIcon from "@mui/icons-material/ShareRounded";

import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import IconButton from "@mui/material/IconButton";

export default function TopbarActions() {
    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",
                gap: 1,
            }}
        >
            <IconButton size="small">
                <AutorenewRoundedIcon fontSize="small" />
            </IconButton>

            <IconButton size="small">
                <ShareRoundedIcon fontSize="small" />
            </IconButton>

            <Button
                variant="contained"
                size="small"
            >
                Explain Dashboard
            </Button>

            <IconButton size="small">
                <SearchRoundedIcon fontSize="small" />
            </IconButton>

            <IconButton size="small">
                <NotificationsNoneRoundedIcon fontSize="small" />
            </IconButton>

            <IconButton size="small">
                <DarkModeRoundedIcon fontSize="small" />
            </IconButton>
        </Box>
    );
}