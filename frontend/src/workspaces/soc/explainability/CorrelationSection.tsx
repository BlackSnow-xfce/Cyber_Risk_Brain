import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { Correlation } from "@/reasoning";

interface CorrelationSectionProps {
    correlations: readonly Correlation[];
}

export default function CorrelationSection({
    correlations,
}: CorrelationSectionProps) {
    return (
        <PipelineStage
            icon={pipelineIcons.correlation}
            title="Correlation"
            description="Relationships to other entities"
            countLabel={`${correlations.length} Relations`}
            status={correlations.length > 0 ? "Completed" : "Pending"}
            items={correlations.map((correlation) => correlation.type)}
        />
    );
}
