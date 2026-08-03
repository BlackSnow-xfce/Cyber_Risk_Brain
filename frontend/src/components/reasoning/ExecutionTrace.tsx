import Stack from "@mui/material/Stack";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import type { ExecutionTraceResult } from "@/engine";

import ExecutionTraceItem from "./ExecutionTraceItem";

interface ExecutionTraceProps {
    trace: ExecutionTraceResult;
}

export default function ExecutionTrace({ trace }: ExecutionTraceProps) {
    return (
        <DashboardWidget
            title="Execution Trace"
            subtitle="Chronological deterministic rule execution"
        >
            <Stack spacing={2}>
                {trace.entries.map((entry) => (
                    <ExecutionTraceItem
                        key={`${entry.executionOrder}-${entry.ruleName}`}
                        entry={entry}
                    />
                ))}
            </Stack>
        </DashboardWidget>
    );
}
