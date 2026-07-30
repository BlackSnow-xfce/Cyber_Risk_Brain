import type { PropsWithChildren, ReactNode } from "react";

import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface DecisionSectionProps extends PropsWithChildren {
    title: string;
    subtitle?: string;
    action?: ReactNode;
}

export default function DecisionSection({
    title,
    subtitle,
    action,
    children,
}: DecisionSectionProps) {
    return (
        <Stack spacing={2}>
            <Stack
                direction="row"
                sx={{
                    justifyContent: "space-between",
                    alignItems: "center",
                }}
            >
                <Stack spacing={0.5}>
                    <Typography variant="h6">
                        {title}
                    </Typography>

                    {subtitle && (
                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {subtitle}
                        </Typography>
                    )}
                </Stack>

                {action}
            </Stack>

            {children}
        </Stack>
    );
}