import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import Chip from "@mui/material/Chip";

interface DecisionHeaderProps {
    title: string;
    status: string;
    subtitle?: string;
}

export default function DecisionHeader({
    title,
    status,
    subtitle,
}: DecisionHeaderProps) {
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
                    <Typography
                        variant="h5"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
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

                <Chip
                    label={status}
                    color="primary"
                    variant="filled"
                />
            </Stack>
        </Stack>
    );
}