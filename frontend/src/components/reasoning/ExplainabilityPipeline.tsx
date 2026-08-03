import Stack from "@mui/material/Stack";

import type { Entity } from "@/domain";
import type { KnowledgeBinding, KnowledgeItem } from "@/knowledge";

import PipelineConnector from "./PipelineConnector";
import { pipelineIcons } from "./PipelineIcons";
import PipelineStage, { type PipelineStageProps } from "./PipelineStage";

interface ExplainabilityPipelineProps {
    entity: Entity;
    knowledge: readonly KnowledgeItem[];
    knowledgeBindings: readonly KnowledgeBinding[];
}

export default function ExplainabilityPipeline({
    entity,
    knowledge,
    knowledgeBindings,
}: ExplainabilityPipelineProps) {
    const stages: readonly PipelineStageProps[] = [
        {
            icon: pipelineIcons.knowledge,
            title: "Knowledge",
            description: "Relevant cybersecurity knowledge",
            countLabel: `${knowledge.length} Items`,
            status: knowledge.length > 0 ? "Completed" : "Pending",
            items: knowledge.map((item) => item.type),
        },
        {
            icon: pipelineIcons.knowledgeBinding,
            title: "Knowledge Binding",
            description: "Knowledge connected to this finding",
            countLabel: `${knowledgeBindings.length} Bindings`,
            status:
                knowledgeBindings.length > 0 ? "Completed" : "Pending",
            items: knowledgeBindings.map((binding) => binding.type),
        },
        {
            icon: pipelineIcons.evidence,
            title: "Evidence",
            description: "Observed facts for this finding",
            countLabel: `${entity.evidence.length} Items`,
            status: entity.evidence.length > 0 ? "Completed" : "Pending",
            items: entity.evidence.map((evidence) => evidence.type),
        },
        {
            icon: pipelineIcons.correlation,
            title: "Correlation",
            description: "Relationships to other entities",
            countLabel: `${entity.correlations.length} Relations`,
            status:
                entity.correlations.length > 0 ? "Completed" : "Pending",
            items: entity.correlations.map((correlation) => correlation.type),
        },
        {
            icon: pipelineIcons.inference,
            title: "Inference",
            description: "Derived professional insights",
            countLabel: `${entity.inference?.length ?? 0} Items`,
            status:
                (entity.inference?.length ?? 0) > 0
                    ? "Completed"
                    : "Pending",
            items: entity.inference?.map((inference) => inference.type) ?? [],
        },
        {
            icon: pipelineIcons.reasoning,
            title: "Reasoning",
            description: "Traceable analysis steps",
            countLabel: `${entity.reasoning?.steps.length ?? 0} Steps`,
            status: entity.reasoning ? "Completed" : "Pending",
            items:
                entity.reasoning?.steps.map((step) => step.title) ?? [],
        },
        {
            icon: pipelineIcons.decision,
            title: "Decision",
            description: "Professional assessment outcome",
            countLabel: entity.decision?.type ?? "No decision",
            status:
                entity.decision?.state === "Proposed"
                    ? "Active"
                    : entity.decision
                      ? "Completed"
                      : "Pending",
            items: entity.decision ? [entity.decision.priority] : [],
        },
        {
            icon: pipelineIcons.recommendation,
            title: "Recommendation",
            description: "Recommended response",
            countLabel: entity.recommendation?.type ?? "No recommendation",
            status: entity.recommendation ? "Completed" : "Pending",
            items: entity.recommendation
                ? [entity.recommendation.priority]
                : [],
        },
    ];

    return (
        <Stack component="section" aria-label="Explainability pipeline">
            {stages.map((stage, index) => (
                <Stack key={stage.title}>
                    {index > 0 && <PipelineConnector />}
                    <PipelineStage {...stage} />
                </Stack>
            ))}
        </Stack>
    );
}
