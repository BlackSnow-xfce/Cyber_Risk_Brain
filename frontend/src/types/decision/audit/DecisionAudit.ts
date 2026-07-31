import type { AuditEntry } from "./AuditEntry";

export interface DecisionAudit {
    entries: AuditEntry[];

    checksum?: string;

    signature?: string;
}