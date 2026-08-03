import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

interface DecisionTimelineProps {
    items: string[];
}

export default function DecisionTimeline({
    items,
}: DecisionTimelineProps) {
    return (
        <Stack spacing={2}>
            {items.map((item) => (
                <Stack
                    key={item}
                    direction="row"
                    spacing={2}
                    sx={{
                        alignItems: "flex-start",
                    }}
                >
                    <Typography
                        sx={{
                            minWidth: 24,
                            fontWeight: 700,
                            color: "primary.main",
                        }}
                    >
                        •
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {item}
                    </Typography>
                </Stack>
            ))}
        </Stack>
    );
}
