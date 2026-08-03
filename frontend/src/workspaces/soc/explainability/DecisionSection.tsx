import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { Decision } from "@/decision";

interface DecisionSectionProps {
    decision: Decision | undefined;
}

export default function DecisionSection({ decision }: DecisionSectionProps) {
    const status =
        decision?.state === "Proposed"
            ? "Active"
            : decision
              ? "Completed"
              : "Pending";

    return (
        <PipelineStage
            icon={pipelineIcons.decision}
            title="Decision"
            description="Professional assessment outcome"
            countLabel={decision?.type ?? "No decision"}
            status={status}
            items={decision ? [decision.priority] : []}
        />
    );
}
