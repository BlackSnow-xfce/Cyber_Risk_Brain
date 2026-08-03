import Stack from "@mui/material/Stack";

import {
    PipelineConnector,
    pipelineIcons,
    PipelineStage,
} from "@/components/reasoning";
import type { KnowledgeBinding, KnowledgeItem } from "@/knowledge";

interface KnowledgeSectionProps {
    knowledge: readonly KnowledgeItem[];
    bindings: readonly KnowledgeBinding[];
}

export default function KnowledgeSection({
    knowledge,
    bindings,
}: KnowledgeSectionProps) {
    return (
        <Stack>
            <PipelineStage
                icon={pipelineIcons.knowledge}
                title="Knowledge"
                description="Relevant cybersecurity knowledge"
                countLabel={`${knowledge.length} Items`}
                status={knowledge.length > 0 ? "Completed" : "Pending"}
                items={knowledge.map((item) => item.type)}
            />
            <PipelineConnector />
            <PipelineStage
                icon={pipelineIcons.knowledgeBinding}
                title="Knowledge Binding"
                description="Knowledge connected to the selected entity"
                countLabel={`${bindings.length} Bindings`}
                status={bindings.length > 0 ? "Completed" : "Pending"}
                items={bindings.map((binding) => binding.type)}
            />
        </Stack>
    );
}
