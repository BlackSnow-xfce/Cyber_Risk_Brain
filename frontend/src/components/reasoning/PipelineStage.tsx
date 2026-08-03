import type { ComponentProps } from "react";

import PipelineCard from "./PipelineCard";

export type PipelineStageProps = ComponentProps<typeof PipelineCard>;

export default function PipelineStage(props: PipelineStageProps) {
    return <PipelineCard {...props} />;
}
