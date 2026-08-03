import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { ReasoningChain } from "@/reasoning";

interface ReasoningSectionProps {
    reasoning: ReasoningChain | undefined;
}

export default function ReasoningSection({
    reasoning,
}: ReasoningSectionProps) {
    return (
        <PipelineStage
            icon={pipelineIcons.reasoning}
            title="Reasoning"
            description="Traceable analysis steps"
            countLabel={`${reasoning?.steps.length ?? 0} Steps`}
            status={reasoning ? "Completed" : "Pending"}
            items={reasoning?.steps.map((step) => step.title) ?? []}
        />
    );
}
