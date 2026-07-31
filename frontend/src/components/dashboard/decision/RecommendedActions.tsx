import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Decision } from "@/types/decision";

interface RecommendedActionsProps {
    decision: Decision;
}

export default function RecommendedActions({
    decision,
}: RecommendedActionsProps) {
    const actions = decision.actions.actions;

    if (actions.length === 0) {
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
                {actions.map((action, index) => (
                    <Paper
                        key={action.id}
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
                                    bgcolor: "primary.main",
                                    color:
                                        "primary.contrastText",
                                    alignItems: "center",
                                    justifyContent: "center",
                                    flexShrink: 0,
                                }}
                            >
                                <Typography variant="subtitle2">
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
        justifyContent: "space-between",
        alignItems: "center",
    }}
>
                                    <Typography
                                        variant="subtitle1"
                                        sx={{
                                            fontWeight: 600,
                                        }}
                                    >
                                        {action.title}
                                    </Typography>

                                    <Typography
                                        variant="overline"
                                        color={
                                            action.automation
                                                ? "success.main"
                                                : "warning.main"
                                        }
                                    >
                                        {action.automation
                                            ? "AUTOMATED"
                                            : "MANUAL"}
                                    </Typography>
                                </Stack>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {action.description}
                                </Typography>
                            </Stack>
                        </Stack>
                    </Paper>
                ))}
            </Stack>

            {decision.actions.executionSummary && (
                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {decision.actions.executionSummary}
                </Typography>
            )}
        </Stack>
    );
}