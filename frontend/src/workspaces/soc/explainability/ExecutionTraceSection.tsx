import { ExecutionTrace } from "@/components/reasoning";
import type { ExecutionTraceResult } from "@/engine";

interface ExecutionTraceSectionProps {
    trace: ExecutionTraceResult;
}

export default function ExecutionTraceSection({
    trace,
}: ExecutionTraceSectionProps) {
    return <ExecutionTrace trace={trace} />;
}
