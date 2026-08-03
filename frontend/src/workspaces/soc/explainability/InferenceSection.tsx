import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { Inference } from "@/inference";

interface InferenceSectionProps {
    inferences: readonly Inference[];
}

export default function InferenceSection({
    inferences,
}: InferenceSectionProps) {
    return (
        <PipelineStage
            icon={pipelineIcons.inference}
            title="Inference"
            description="Derived professional insights"
            countLabel={`${inferences.length} Items`}
            status={inferences.length > 0 ? "Completed" : "Pending"}
            items={inferences.map((inference) => inference.type)}
        />
    );
}
