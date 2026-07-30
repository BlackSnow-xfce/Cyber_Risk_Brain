import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { DecisionResponse } from "@/types/decision/DecisionResponse";

interface RecommendedActionsProps {
    decision: DecisionResponse;
}

export default function RecommendedActions({
    decision,
}: RecommendedActionsProps) {
    if (decision.recommendations.length === 0) {
        return (
            <Stack spacing={3}>
                <Stack spacing={0.5}>
                    <Typography
                        variant="overline"
                        color="primary"
                    >
                        Response Playbook
                    </Typography>

                    <Typography variant="h5">
                        Recommended Actions
                    </Typography>

                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        No actions are currently required.
                    </Typography>
                </Stack>
            </Stack>
        );
    }

    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography
                    variant="overline"
                    color="primary"
                >
                    Response Playbook
                </Typography>

                <Typography variant="h5">
                    Recommended Actions
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Ordered response steps proposed by the
                    decision engine.
                </Typography>
            </Stack>

            <Stack spacing={2}>
                {decision.recommendations.map(
                    (recommendation, index) => (
                        <Paper
                            key={recommendation.id}
                            variant="outlined"
                            sx={{
                                p: 2.5,
                                borderRadius: 2,
                            }}
                        >
                            <Stack
                                direction="row"
                                spacing={2}
                                sx={{
                                    alignItems: "flex-start",
                                }}
                            >
                                <Stack
                                    sx={{
                                        width: 36,
                                        height: 36,
                                        borderRadius: "50%",
                                        bgcolor:
                                            "primary.main",
                                        color:
                                            "primary.contrastText",
                                        alignItems:
                                            "center",
                                        justifyContent:
                                            "center",
                                        flexShrink: 0,
                                    }}
                                >
                                    <Typography
                                        variant="subtitle2"
                                    >
                                        {index + 1}
                                    </Typography>
                                </Stack>

                                <Stack
                                    spacing={0.75}
                                    sx={{
                                        flex: 1,
                                    }}
                                >
                                    <Stack
                                        direction="row"
                                        sx={{
                                            justifyContent:
                                                "space-between",
                                            alignItems:
                                                "center",
                                        }}
                                    >
                                        <Typography
                                            variant="subtitle1"
                                            sx={{
                                                fontWeight:
                                                    600,
                                            }}
                                        >
                                            {
                                                recommendation.title
                                            }
                                        </Typography>

                                        <Typography
                                            variant="overline"
                                            color={
                                                recommendation.automated
                                                    ? "success.main"
                                                    : "warning.main"
                                            }
                                        >
                                            {recommendation.automated
                                                ? "AUTOMATED"
                                                : "MANUAL"}
                                        </Typography>
                                    </Stack>

                                    <Typography
                                        variant="body2"
                                        color="text.secondary"
                                    >
                                        {
                                            recommendation.description
                                        }
                                    </Typography>
                                </Stack>
                            </Stack>
                        </Paper>
                    )
                )}
            </Stack>
        </Stack>
    );
}