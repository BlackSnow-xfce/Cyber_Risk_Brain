import type { ExecutionTraceEntry } from "./ExecutionTraceEntry";

export interface ExecutionTraceResult {
    entries: readonly ExecutionTraceEntry[];
}
