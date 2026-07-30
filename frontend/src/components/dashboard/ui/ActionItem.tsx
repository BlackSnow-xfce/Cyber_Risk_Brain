import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface ActionItemProps {
    title: string;
    description?: string;
}

export default function ActionItem({
    title,
    description,
}: ActionItemProps) {
    return (
        <Stack
            spacing={0.5}
            sx={{
                p: 2,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                bgcolor: "background.paper",
            }}
        >
            <Typography
                variant="subtitle2"
                sx={{
                    fontWeight: 600,
                }}
            >
                {title}
            </Typography>

            {description && (
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {description}
                </Typography>
            )}
        </Stack>
    );
}