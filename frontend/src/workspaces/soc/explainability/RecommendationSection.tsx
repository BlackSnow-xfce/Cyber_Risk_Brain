import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { Recommendation } from "@/recommendation";

interface RecommendationSectionProps {
    recommendation: Recommendation | undefined;
}

export default function RecommendationSection({
    recommendation,
}: RecommendationSectionProps) {
    return (
        <PipelineStage
            icon={pipelineIcons.recommendation}
            title="Recommendation"
            description="Recommended response"
            countLabel={recommendation?.type ?? "No recommendation"}
            status={recommendation ? "Completed" : "Pending"}
            items={recommendation ? [recommendation.priority] : []}
        />
    );
}
