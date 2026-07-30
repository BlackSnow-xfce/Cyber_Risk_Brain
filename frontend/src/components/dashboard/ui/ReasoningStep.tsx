import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface ReasoningStepProps {
    step: number;
    title: string;
    description: string;
}

export default function ReasoningStep({
    step,
    title,
    description,
}: ReasoningStepProps) {
    return (
        <Stack
            direction="row"
            spacing={2}
            sx={{
                alignItems: "flex-start",
                p: 2,
                border: "1px solid",
                borderColor: "divider",
                borderRadius: 2,
                bgcolor: "background.paper",
            }}
        >
            <Typography
                variant="h6"
                sx={{
                    minWidth: 32,
                    fontWeight: 700,
                    color: "primary.main",
                }}
            >
                {step}
            </Typography>

            <Stack spacing={0.5}>
                <Typography
                    variant="subtitle2"
                    sx={{
                        fontWeight: 600,
                    }}
                >
                    {title}
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {description}
                </Typography>
            </Stack>
        </Stack>
    );
}