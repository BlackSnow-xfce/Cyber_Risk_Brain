import Paper from "@mui/material/Paper";
import type { PaperProps } from "@mui/material/Paper";

export default function Panel({
    children,
    sx,
    ...props
}: PaperProps) {
    return (
        <Paper
            elevation={0}
            sx={{
                p: 2,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                backgroundColor: "background.paper",
                ...sx,
            }}
            {...props}
        >
            {children}
        </Paper>
    );
}