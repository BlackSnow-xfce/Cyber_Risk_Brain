import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";

import type { Decision } from "@/types/decision";

interface RecommendedActionsProps {
    decision: Decision;
}

export default function RecommendedActions({
    decision,
}: RecommendedActionsProps) {
    const actions = decision.actions.actions;

    return (
        <DecisionSection
            title="Response Playbook"
            subtitle="Recommended Actions"
        >
            <Stack spacing={2}>
                {actions.length === 0 ? (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        No actions are currently required.
                    </Typography>
                ) : (
                    actions.map((action, index) => (
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
                                        color: "primary.contrastText",
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
                                        minWidth: 0,
                                    }}
                                >
                                    <Stack
                                        direction="row"
                                        spacing={2}
                                        sx={{
                                            justifyContent:
                                                "space-between",
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
                                            sx={{
                                                flexShrink: 0,
                                            }}
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
                    ))
                )}

                {decision.actions.executionSummary && (
                    <Typography
                        variant="body2"
                        color="text.secondary"
                    >
                        {decision.actions.executionSummary}
                    </Typography>
                )}
            </Stack>
        </DecisionSection>
    );
}