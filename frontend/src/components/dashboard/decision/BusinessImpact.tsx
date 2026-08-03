import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";

import type { Decision } from "@/types/decision";

interface BusinessImpactProps {
    decision: Decision;
}

export default function BusinessImpact({
    decision,
}: BusinessImpactProps) {
    const impact = decision.impact;

    const impactCards = [
        {
            title: "Operational Impact",
            value: impact.operational,
        },
        {
            title: "Financial Impact",
            value: impact.financial,
        },
        {
            title: "Regulatory Impact",
            value: impact.regulatory,
        },
        {
            title: "Reputational Impact",
            value: impact.reputational,
        },
    ].filter(
        (
            item,
        ): item is {
            title: string;
            value: string;
        } => Boolean(item.value),
    );

    return (
        <DecisionSection
            title="Business Impact"
            subtitle="Organizational consequences"
        >
            <Stack spacing={2}>
                {impactCards.map((item) => (
                    <Paper
                        key={item.title}
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
                                {item.title}
                            </Typography>

                            <Typography
                                variant="body2"
                                color="text.secondary"
                            >
                                {item.value}
                            </Typography>
                        </Stack>
                    </Paper>
                ))}

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
                            sx={{
                                fontWeight: 600,
                            }}
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
        </DecisionSection>
    );
}