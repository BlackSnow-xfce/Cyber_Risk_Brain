import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { ThreatIntelligence } from "./ThreatIntelligence";
import ThreatIntelligenceListItem from "./ThreatIntelligenceListItem";

interface ThreatIntelligenceListProps {
    threats: readonly ThreatIntelligence[];
    selectedThreatId: string | null;
    onSelect: (threat: ThreatIntelligence) => void;
}

export default function ThreatIntelligenceList({
    threats,
    selectedThreatId,
    onSelect,
}: ThreatIntelligenceListProps) {
    return (
        <Panel
            component="section"
            aria-labelledby="threat-intelligence-list-title"
        >
            <Stack spacing={2}>
                <Typography
                    id="threat-intelligence-list-title"
                    variant="h6"
                >
                    Threat Intelligence List
                </Typography>

                {threats.map((threat) => (
                    <ThreatIntelligenceListItem
                        key={threat.id}
                        threat={threat}
                        selected={threat.id === selectedThreatId}
                        onSelect={onSelect}
                    />
                ))}
            </Stack>
        </Panel>
    );
}
