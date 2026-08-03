import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Decision } from "@/types/decision";

interface DecisionHeroProps {
    decision: Decision;
}

export default function DecisionHero({
    decision,
}: DecisionHeroProps) {
    const metrics = [
        {
            label: "PRIORITY",
            value: decision.risk.priority,
        },
        {
            label: "CONFIDENCE",
            value: `${decision.confidence.score}%`,
        },
        {
            label: "ENGINE",
            value: decision.metadata.engineVersion,
        },
        {
            label: "MODEL",
            value: decision.metadata.modelVersion,
        },
    ];

    return (
        <Stack
            spacing={3}
            sx={{
                p: 4,
                borderRadius: 3,
                border: "1px solid",
                borderColor: "divider",
                bgcolor: "background.paper",
            }}
        >
            <Stack
                direction="row"
                sx={{
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: 3,
                }}
            >
                <Stack
                    spacing={1}
                    sx={{
                        minWidth: 0,
                        flex: 1,
                    }}
                >
                    <Typography
                        variant="overline"
                        color="primary"
                    >
                        AI DECISION
                    </Typography>

                    <Typography
                        variant="h3"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {decision.summary.title}
                    </Typography>

                    <Typography
                        variant="body1"
                        color="text.secondary"
                        sx={{
                            maxWidth: 900,
                            lineHeight: 1.8,
                        }}
                    >
                        {decision.summary.description}
                    </Typography>
                </Stack>

                <Stack
                    spacing={1}
                    sx={{
                        alignItems: "flex-end",
                        flexShrink: 0,
                    }}
                >
                    <Chip
                        label={decision.status.state}
                        color="primary"
                    />

                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        Decision Status
                    </Typography>
                </Stack>
            </Stack>

            <Divider />

            <Stack
                direction="row"
                sx={{
                    flexWrap: "wrap",
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                {metrics.map((metric, index) => (
                    <Stack
                        key={metric.label}
                        spacing={0.5}
                        sx={{
                            flex: 1,
                            minWidth: 180,
                            p: 2,
                            borderLeft:
                                index === 0
                                    ? "none"
                                    : "1px solid",
                            borderColor: "divider",
                        }}
                    >
                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            {metric.label}
                        </Typography>

                        <Typography variant="h6">
                            {metric.value}
                        </Typography>
                    </Stack>
                ))}
            </Stack>

            <Divider />

            <Stack spacing={1}>
                <Typography
                    variant="overline"
                    color="primary"
                >
                    Situation
                </Typography>

                <Typography
                    variant="body1"
                    color="text.secondary"
                >
                    {decision.explainability.summary}
                </Typography>
            </Stack>
        </Stack>
    );
}