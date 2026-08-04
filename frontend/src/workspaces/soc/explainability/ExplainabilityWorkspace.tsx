import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";

import {
    knowledgeBindingRepository,
    knowledgeRepository,
} from "@/knowledge";
import { defaultReasoningOrchestrator } from "@/reasoning/DefaultReasoningOrchestrator";

import { useSOCWorkspace } from "../SOCWorkspaceContext";
import { findingRepository } from "../findings/MockFindingRepository";
import ExecutionTraceSection from "./ExecutionTraceSection";
import ExplainabilityOverview from "./ExplainabilityOverview";
import ExplainabilityToolbar from "./ExplainabilityToolbar";

export default function ExplainabilityWorkspace() {
    const { selectedFinding } = useSOCWorkspace();
    const findings = findingRepository.getFindings();
    const entity = selectedFinding ?? findings[0] ?? null;

    if (!entity) {
        return null;
    }

    const bindings =
        knowledgeBindingRepository.getBindingsByEntityId(entity.id);
    const knowledgeIds = new Set(
        bindings.map((binding) => binding.knowledgeItemId),
    );
    const knowledge = knowledgeRepository
        .getKnowledgeItems()
        .filter((item) => knowledgeIds.has(item.id));
    const reasoningSession = defaultReasoningOrchestrator.execute({
        entity,
        knowledge,
        knowledgeBindings: bindings,
        evidence: entity.evidence,
        correlations: entity.correlations,
    });

    return (
        <Stack spacing={2}>
            <ExplainabilityToolbar
                entities={findings}
                selectedEntityId={entity.id}
            />
            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        xl: "minmax(0, 1.2fr) minmax(360px, 0.8fr)",
                    },
                    gap: 2,
                    alignItems: "start",
                    minWidth: 0,
                }}
            >
                <ExplainabilityOverview
                    entity={entity}
                    knowledge={knowledge}
                    bindings={bindings}
                />
                {reasoningSession.result && (
                    <ExecutionTraceSection
                        trace={reasoningSession.result.executionTrace}
                    />
                )}
            </Box>
        </Stack>
    );
}
