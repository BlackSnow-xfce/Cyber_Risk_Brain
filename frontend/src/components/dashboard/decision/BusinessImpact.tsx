import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { Decision } from "@/types/decision";

interface BusinessImpactProps {
    decision: Decision;
}

export default function BusinessImpact({
    decision,
}: BusinessImpactProps) {
    const impact = decision.impact;

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
                            sx={{ fontWeight: 600 }}
                        >
                            Operational Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.operational}
                        </Typography>
                    </Stack>
                </Paper>

                {impact.financial && (
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
                                sx={{ fontWeight: 600 }}
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
                )}

                {impact.regulatory && (
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
                                sx={{ fontWeight: 600 }}
                            >
                                Regulatory Impact
                            </Typography>

                            <Typography
                                variant="body2"
                                color="text.secondary"
                            >
                                {impact.regulatory}
                            </Typography>
                        </Stack>
                    </Paper>
                )}

                {impact.reputational && (
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
                                sx={{ fontWeight: 600 }}
                            >
                                Reputational Impact
                            </Typography>

                            <Typography
                                variant="body2"
                                color="text.secondary"
                            >
                                {impact.reputational}
                            </Typography>
                        </Stack>
                    </Paper>
                )}

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
                            sx={{ fontWeight: 600 }}
                        >
                            CIA Impact
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            <strong>Confidentiality:</strong>{" "}
                            {impact.confidentiality}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            <strong>Integrity:</strong>{" "}
                            {impact.integrity}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            <strong>Availability:</strong>{" "}
                            {impact.availability}
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
                            sx={{ fontWeight: 600 }}
                        >
                            Overall Assessment
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {impact.narrative}
                        </Typography>
                    </Stack>
                </Paper>
            </Stack>
        </Stack>
    );
}