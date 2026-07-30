import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { DecisionResponse } from "@/types/decision/DecisionResponse";

interface BusinessImpactProps {
    decision: DecisionResponse;
}

export default function BusinessImpact({
    decision,
}: BusinessImpactProps) {
    const impact = decision.businessImpact;

    return (
        <Stack spacing={3}>
            <Stack spacing={0.5}>
                <Typography
                    variant="overline"
                    color="primary"
                >
                    Business Impact
                </Typography>

                <Typography variant="h5">
                    Organizational consequences
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    Estimated business impact if no action is
                    taken.
                </Typography>
            </Stack>

            <Stack spacing={2}>
                <Paper
                    variant="outlined"
                    sx={{
                        p: 2.5,
                        borderRadius: 2,
                    }}
                >
                    <Stack spacing={0.5}>
                        <Typography
                            variant="subtitle1"
                            sx={{
                                fontWeight: 600,
                            }}
                        >
                            Operational Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.operations}
                        </Typography>
                    </Stack>
                </Paper>

                <Paper
                    variant="outlined"
                    sx={{
                        p: 2.5,
                        borderRadius: 2,
                    }}
                >
                    <Stack spacing={0.5}>
                        <Typography
                            variant="subtitle1"
                            sx={{
                                fontWeight: 600,
                            }}
                        >
                            Financial Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.financial}
                        </Typography>
                    </Stack>
                </Paper>

                <Paper
                    variant="outlined"
                    sx={{
                        p: 2.5,
                        borderRadius: 2,
                    }}
                >
                    <Stack spacing={0.5}>
                        <Typography
                            variant="subtitle1"
                            sx={{
                                fontWeight: 600,
                            }}
                        >
                            Compliance Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.compliance}
                        </Typography>
                    </Stack>
                </Paper>

                <Paper
                    variant="outlined"
                    sx={{
                        p: 2.5,
                        borderRadius: 2,
                    }}
                >
                    <Stack spacing={0.5}>
                        <Typography
                            variant="subtitle1"
                            sx={{
                                fontWeight: 600,
                            }}
                        >
                            Reputation Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.reputation}
                        </Typography>
                    </Stack>
                </Paper>
            </Stack>
        </Stack>
    );
}