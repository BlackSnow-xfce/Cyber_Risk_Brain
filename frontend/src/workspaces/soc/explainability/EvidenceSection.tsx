import { pipelineIcons, PipelineStage } from "@/components/reasoning";
import type { Evidence } from "@/reasoning";

interface EvidenceSectionProps {
    evidence: readonly Evidence[];
}

export default function EvidenceSection({ evidence }: EvidenceSectionProps) {
    return (
        <PipelineStage
            icon={pipelineIcons.evidence}
            title="Evidence"
            description="Observed facts for the selected entity"
            countLabel={`${evidence.length} Items`}
            status={evidence.length > 0 ? "Completed" : "Pending"}
            items={evidence.map((item) => item.type)}
        />
    );
}
