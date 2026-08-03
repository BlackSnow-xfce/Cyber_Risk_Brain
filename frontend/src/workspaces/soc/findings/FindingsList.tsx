import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Finding } from "./Finding";
import FindingListItem from "./FindingListItem";

interface FindingsListProps {
    findings: readonly Finding[];
    selectedFindingId: string | null;
    onSelect: (finding: Finding) => void;
}

export default function FindingsList({
    findings,
    selectedFindingId,
    onSelect,
}: FindingsListProps) {
    return (
        <Panel component="section" aria-labelledby="findings-list-title">
            <Stack spacing={2}>
                <Typography
                    id="findings-list-title"
                    variant="h6"
                >
                    Findings List
                </Typography>

                {findings.map((finding) => (
                    <FindingListItem
                        key={finding.id}
                        finding={finding}
                        selected={finding.id === selectedFindingId}
                        onSelect={onSelect}
                    />
                ))}
            </Stack>
        </Panel>
    );
}
