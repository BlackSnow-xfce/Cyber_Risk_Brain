import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import BusinessImpact from "./BusinessImpact";
import DecisionHero from "./DecisionHero";
import DecisionTimeline from "./DecisionTimeline";
import EvidenceChips from "./EvidenceChips";
import ExecutiveSummary from "./ExecutiveSummary";
import Explainability from "./Explainability";
import RecommendedActions from "./RecommendedActions";

import type { Decision } from "@/types/decision";

interface DecisionWorkspaceProps {
    decision: Decision;
}

export default function DecisionWorkspace({
    decision,
}: DecisionWorkspaceProps) {
    return (
        <Stack
            spacing={5}
            sx={{
                width: "100%",
            }}
        >
            <DecisionHero decision={decision} />

            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        lg: "minmax(0, 1.65fr) minmax(320px, 0.75fr)",
                    },
                    gap: {
                        xs: 4,
                        lg: 5,
                    },
                    alignItems: "start",
                    width: "100%",
                }}
            >
                <Stack
                    spacing={5}
                    sx={{
                        minWidth: 0,
                    }}
                >
                    <ExecutiveSummary decision={decision} />

                    <EvidenceChips decision={decision} />

                    <BusinessImpact decision={decision} />

                    <RecommendedActions decision={decision} />
                </Stack>

                <Box
                    component="aside"
                    sx={{
                        minWidth: 0,
                        position: {
                            xs: "static",
                            lg: "sticky",
                        },
                        top: {
                            lg: 96,
                        },
                    }}
                >
                    <Stack spacing={5}>
                        <Explainability decision={decision} />

                        <DecisionTimeline />
                    </Stack>
                </Box>
            </Box>
        </Stack>
    );
}