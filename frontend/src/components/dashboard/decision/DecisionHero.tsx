import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { DecisionResponse } from "@/types/decision/DecisionResponse";

interface DecisionHeroProps {
    decision: DecisionResponse;
}

export default function DecisionHero({
    decision,
}: DecisionHeroProps) {
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
                }}
            >
                <Stack spacing={1}>
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
                        {decision.decision.title}
                    </Typography>

                    <Typography
                        variant="body1"
                        color="text.secondary"
                        sx={{
                            maxWidth: 900,
                            lineHeight: 1.8,
                        }}
                    >
                        {decision.decision.description}
                    </Typography>
                </Stack>

                <Stack
                    spacing={1}
                    sx={{
                        alignItems: "flex-end",
                    }}
                >
                    <Chip
                        label={decision.status.toUpperCase()}
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
                    border: "1px solid",
                    borderColor: "divider",
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                <Stack
                    spacing={0.5}
                    sx={{
                        flex: 1,
                        p: 2,
                    }}
                >
                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        PRIORITY
                    </Typography>

                    <Typography variant="h6">
                        {decision.priority.toUpperCase()}
                    </Typography>
                </Stack>

                <Stack
                    spacing={0.5}
                    sx={{
                        flex: 1,
                        p: 2,
                        borderLeft: "1px solid",
                        borderColor: "divider",
                    }}
                >
                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        CONFIDENCE
                    </Typography>

                    <Typography variant="h6">
                        {decision.confidence}%
                    </Typography>
                </Stack>

                <Stack
                    spacing={0.5}
                    sx={{
                        flex: 1,
                        p: 2,
                        borderLeft: "1px solid",
                        borderColor: "divider",
                    }}
                >
                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        ENGINE
                    </Typography>

                    <Typography variant="h6">
                        {decision.metadata.engine}
                    </Typography>
                </Stack>

                <Stack
                    spacing={0.5}
                    sx={{
                        flex: 1,
                        p: 2,
                        borderLeft: "1px solid",
                        borderColor: "divider",
                    }}
                >
                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        MODEL
                    </Typography>

                    <Typography variant="h6">
                        {decision.metadata.model}
                    </Typography>
                </Stack>
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
                    {decision.summary}
                </Typography>
            </Stack>

            <Divider />

            <Typography
                variant="body2"
                color="text.secondary"
            >
                Continue below for evidence, business impact,
                recommendations, reasoning and timeline.
            </Typography>
        </Stack>
    );
}