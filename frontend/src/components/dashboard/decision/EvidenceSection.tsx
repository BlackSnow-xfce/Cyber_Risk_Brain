import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import DecisionSection from "@/components/dashboard/ui/DecisionSection";
import EvidenceChip from "@/components/dashboard/ui/EvidenceChip";

import type { DecisionResponse } from "@/types/decision/DecisionResponse";

interface EvidenceSectionProps {
    decision: DecisionResponse;
}

export default function EvidenceSection({
    decision,
}: EvidenceSectionProps) {
    return (
        <DecisionSection
            title="Evidence"
            subtitle="Facts supporting the decision"
        >
            <Stack spacing={2}>
                {decision.evidence.map((item) => (
                    <Stack
                        key={item.id}
                        spacing={1}
                        sx={{
                            p: 2,
                            border: "1px solid",
                            borderColor: "divider",
                            borderRadius: 2,
                        }}
                    >
                        <EvidenceChip label={item.title} />

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {item.value}
                        </Typography>

                        <Typography
                            variant="caption"
                            color="text.secondary"
                        >
                            Confidence: {item.confidence}%
                        </Typography>
                    </Stack>
                ))}
            </Stack>
        </DecisionSection>
    );
}