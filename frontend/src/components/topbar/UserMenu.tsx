import Avatar from "@mui/material/Avatar";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

export default function UserMenu() {
    return (
        <Box
            sx={{
                display: "flex",
                alignItems: "center",
                gap: 1.5,
            }}
        >
            <Box>
                <Typography
                    variant="body2"
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    Max Mustermann
                </Typography>

                <Typography
                    variant="caption"
                    color="text.secondary"
                >
                    Security Admin
                </Typography>
            </Box>

            <Avatar
                sx={{
                    width: 40,
                    height: 40,
                }}
            >
                MM
            </Avatar>
        </Box>
    );
}