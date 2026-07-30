import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { DecisionResponse } from "@/types/decision";

interface EvidenceChipsProps {
    decision: DecisionResponse;
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
                {decision.evidence.map((item) => (
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
                                alignItems: "center",
                            }}
                        >
                            <Stack spacing={0.5}>
                                <Typography
                                    variant="subtitle1"
                                    sx={{
                                        fontWeight: 600,
                                    }}
                                >
                                    {item.title}
                                </Typography>

                                <Typography
                                    variant="body2"
                                    color="text.secondary"
                                >
                                    {item.value}
                                </Typography>
                            </Stack>

                            <Typography
                                variant="overline"
                                color="primary"
                            >
                                EVIDENCE
                            </Typography>
                        </Stack>
                    </Paper>
                ))}
            </Stack>
        </Stack>
    );
}