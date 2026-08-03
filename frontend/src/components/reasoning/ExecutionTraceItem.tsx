import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import MetricRow from "@/components/dashboard/ui/MetricRow/MetricRow";
import type { ExecutionTraceEntry } from "@/engine";

import RuleResultBadge from "./RuleResultBadge";
import { traceIcons } from "./TraceIcons";

interface ExecutionTraceItemProps {
    entry: ExecutionTraceEntry;
}

export default function ExecutionTraceItem({
    entry,
}: ExecutionTraceItemProps) {
    const ResultIcon = entry.matched
        ? traceIcons.matched
        : traceIcons.skipped;

    return (
        <Stack spacing={1}>
            <Stack
                direction="row"
                spacing={1}
                sx={{ alignItems: "center", justifyContent: "space-between" }}
            >
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <ResultIcon fontSize="small" color="action" />
                    <Typography variant="subtitle2">
                        {entry.ruleName}
                    </Typography>
                </Stack>
                <RuleResultBadge
                    status={entry.matched ? "MATCHED" : "SKIPPED"}
                />
            </Stack>

            <MetricRow
                label={`Execution ${entry.executionOrder}`}
                value={entry.executedAt.slice(11, 19)}
            />
            <MetricRow label="Duration" value={`${entry.durationMs} ms`} />

            {entry.skippedReason && (
                <Typography variant="body2" color="text.secondary">
                    {entry.skippedReason}
                </Typography>
            )}

            {entry.generatedArtifacts.length > 0 && (
                <Stack spacing={1}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <traceIcons.generated fontSize="small" color="action" />
                        <RuleResultBadge status="GENERATED" />
                    </Stack>
                    {entry.generatedArtifacts.map((artifact) => (
                        <MetricRow
                            key={`${artifact.type}-${artifact.id}`}
                            label={artifact.type}
                            value={artifact.id}
                        />
                    ))}
                </Stack>
            )}

            <Divider />
        </Stack>
    );
}
