import Stack from "@mui/material/Stack";

import { PipelineConnector } from "@/components/reasoning";
import type { Entity } from "@/domain";
import type { KnowledgeBinding, KnowledgeItem } from "@/knowledge";

import CorrelationSection from "./CorrelationSection";
import DecisionSection from "./DecisionSection";
import EvidenceSection from "./EvidenceSection";
import InferenceSection from "./InferenceSection";
import KnowledgeSection from "./KnowledgeSection";
import ReasoningSection from "./ReasoningSection";
import RecommendationSection from "./RecommendationSection";

interface ExplainabilityOverviewProps {
    entity: Entity;
    knowledge: readonly KnowledgeItem[];
    bindings: readonly KnowledgeBinding[];
}

export default function ExplainabilityOverview({
    entity,
    knowledge,
    bindings,
}: ExplainabilityOverviewProps) {
    return (
        <Stack component="section" aria-label="Explainability overview">
            <KnowledgeSection knowledge={knowledge} bindings={bindings} />
            <PipelineConnector />
            <EvidenceSection evidence={entity.evidence} />
            <PipelineConnector />
            <CorrelationSection correlations={entity.correlations} />
            <PipelineConnector />
            <InferenceSection inferences={entity.inference ?? []} />
            <PipelineConnector />
            <ReasoningSection reasoning={entity.reasoning} />
            <PipelineConnector />
            <DecisionSection decision={entity.decision} />
            <PipelineConnector />
            <RecommendationSection recommendation={entity.recommendation} />
        </Stack>
    );
}
