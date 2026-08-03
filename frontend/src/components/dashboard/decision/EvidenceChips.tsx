import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";

import type { Decision } from "@/types/decision";

interface EvidenceChipsProps {
    decision: Decision;
}

export default function EvidenceChips({
    decision,
}: EvidenceChipsProps) {
    return (
        <DecisionSection
            title="Evidence"
            subtitle="Why this decision?"
        >
            <Stack spacing={2}>
                {decision.evidence.items.map((item) => (
                    <Paper
                        key={item.id}
                        variant="outlined"
                        sx={{
                            p: 2.5,
                            borderRadius: 2,
                            bgcolor: "background.paper",
                        }}
                    >
                        <Stack
                            direction="row"
                            spacing={2}
                            sx={{
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                            }}
                        >
                            <Stack
                                spacing={0.75}
                                sx={{
                                    flex: 1,
                                    minWidth: 0,
                                }}
                            >
                                <Typography
                                    variant="subtitle1"
                                    sx={{
                                        fontWeight: 600,
                                    }}
                                >
                                    {item.summary}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {item.source}
                                </Typography>

                                {item.facts.length > 0 && (
                                    <Typography
                                        variant="caption"
                                        color="text.secondary"
                                    >
                                        {item.facts.join(" • ")}
                                    </Typography>
                                )}
                            </Stack>

                            <Typography
                                variant="overline"
                                color="primary"
                                sx={{
                                    flexShrink: 0,
                                }}
                            >
                                {item.type}
                            </Typography>
                        </Stack>
                    </Paper>
                ))}
            </Stack>
        </DecisionSection>
    );
}