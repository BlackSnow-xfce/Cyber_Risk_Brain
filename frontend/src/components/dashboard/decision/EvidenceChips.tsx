import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Decision } from "@/types/decision";

interface EvidenceChipsProps {
    decision: Decision;
}

export default function EvidenceChips({
    decision,
}: EvidenceChipsProps) {
    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography
                    variant="overline"
                    color="primary"
                >
                    Evidence
                </Typography>

                <Typography variant="h5">
                    Why this decision?
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    The following evidence contributed to the
                    AI decision.
                </Typography>
            </Stack>

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
                            sx={{
                                justifyContent: "space-between",
                                alignItems: "flex-start",
                            }}
                        >
                            <Stack spacing={0.75}>
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
                            >
                                {item.type}
                            </Typography>
                        </Stack>
                    </Paper>
                ))}
            </Stack>
        </Stack>
    );
}