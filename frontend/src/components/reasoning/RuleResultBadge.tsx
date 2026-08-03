import StatusBadge from "@/components/dashboard/ui/StatusBadge/StatusBadge";

export type RuleResultStatus = "MATCHED" | "SKIPPED" | "GENERATED";

interface RuleResultBadgeProps {
    status: RuleResultStatus;
}

export default function RuleResultBadge({ status }: RuleResultBadgeProps) {
    const badgeStatus =
        status === "MATCHED"
            ? "healthy"
            : status === "GENERATED"
              ? "live"
              : "offline";

    return <StatusBadge status={badgeStatus} label={status} />;
}
