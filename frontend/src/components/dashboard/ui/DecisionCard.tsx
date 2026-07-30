import type { PropsWithChildren } from "react";

import Paper from "@mui/material/Paper";

export default function DecisionCard({
    children,
}: PropsWithChildren) {
    return (
        <Paper
            elevation={0}
            sx={{
                display: "flex",
                flexDirection: "column",
                gap: 3,

                width: "100%",

                p: 3,

                borderRadius: 3,

                border: "1px solid",
                borderColor: "divider",

                bgcolor: "background.paper",
            }}
        >
            {children}
        </Paper>
    );
}