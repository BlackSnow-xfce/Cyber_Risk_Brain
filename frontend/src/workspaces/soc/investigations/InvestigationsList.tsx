import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Investigation } from "./Investigation";
import InvestigationListItem from "./InvestigationListItem";

interface InvestigationsListProps {
    investigations: readonly Investigation[];
    selectedInvestigationId: string | null;
    onSelect: (investigation: Investigation) => void;
}

export default function InvestigationsList({
    investigations,
    selectedInvestigationId,
    onSelect,
}: InvestigationsListProps) {
    return (
        <Panel
            component="section"
            aria-labelledby="investigations-list-title"
        >
            <Stack spacing={2}>
                <Typography
                    id="investigations-list-title"
                    variant="h6"
                >
                    Investigations List
                </Typography>

                {investigations.map((investigation) => (
                    <InvestigationListItem
                        key={investigation.id}
                        investigation={investigation}
                        selected={
                            investigation.id === selectedInvestigationId
                        }
                        onSelect={onSelect}
                    />
                ))}
            </Stack>
        </Panel>
    );
}
