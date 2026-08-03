import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";

export default function DecisionTimeline() {
    const events = [
        {
            time: "22:14",
            title: "Findings Correlated",
            description:
                "Security findings consolidated from connected data sources.",
        },
        {
            time: "22:15",
            title: "Asset Context Resolved",
            description:
                "Criticality, ownership and business context identified.",
        },
        {
            time: "22:15",
            title: "Threat Intelligence Matched",
            description:
                "External intelligence correlated with current indicators.",
        },
        {
            time: "22:16",
            title: "Business Impact Calculated",
            description:
                "Operational and financial impact estimated.",
        },
        {
            time: "22:16",
            title: "Recommendation Generated",
            description:
                "Decision Engine produced the final recommendation.",
        },
    ];

    return (
        <DecisionSection
            title="Decision Timeline"
            subtitle="Processing Flow"
        >
            <Stack spacing={2}>
                {events.map((event, index) => (
                    <Stack
                        key={`${event.time}-${event.title}`}
                        direction="row"
                        spacing={2}
                        sx={{
                            alignItems: "stretch",
                        }}
                    >
                        <Stack
                            sx={{
                                alignItems: "center",
                                width: 28,
                                flexShrink: 0,
                            }}
                        >
                            <Paper
                                sx={{
                                    width: 12,
                                    height: 12,
                                    borderRadius: "50%",
                                    bgcolor: "primary.main",
                                }}
                            />

                            {index < events.length - 1 && (
                                <Stack
                                    sx={{
                                        flex: 1,
                                        width: 2,
                                        bgcolor: "divider",
                                        mt: 1,
                                        minHeight: 48,
                                    }}
                                />
                            )}
                        </Stack>

                        <Paper
                            variant="outlined"
                            sx={{
                                p: 2,
                                borderRadius: 2,
                                flex: 1,
                            }}
                        >
                            <Stack spacing={0.75}>
                                <Typography
                                    variant="overline"
                                    color="primary"
                                >
                                    {event.time}
                                </Typography>

                                <Typography
                                    variant="subtitle1"
                                    sx={{
                                        fontWeight: 600,
                                    }}
                                >
                                    {event.title}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {event.description}
                                </Typography>
                            </Stack>
                        </Paper>
                    </Stack>
                ))}
            </Stack>
        </DecisionSection>
    );
}