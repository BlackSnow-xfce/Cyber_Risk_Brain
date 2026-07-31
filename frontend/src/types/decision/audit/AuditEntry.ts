export interface AuditEntry {
    id: string;

    actor: string;

    timestamp: string;

    action: string;

    reason?: string;
}