import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { ThreatIntelligence } from "./ThreatIntelligence";

interface ThreatIntelligenceDetailsPanelProps {
    threat: ThreatIntelligence | null;
}

export default function ThreatIntelligenceDetailsPanel({
    threat,
}: ThreatIntelligenceDetailsPanelProps) {
    const detailSections = threat
        ? [
              ["Threat Summary", threat.description],
              ["Intelligence Source", threat.intelligenceSource],
              ["MITRE ATT&CK Mapping", threat.explainability.mitre.join(", ")],
              ["Indicators", threat.indicators],
              ["Related Assets", threat.relatedAssets],
              ["Recommended Actions", threat.recommendation.description],
          ] as const
        : [];

    return (
        <Panel
            component="aside"
            aria-labelledby="threat-intelligence-details-title"
            sx={{ height: "100%" }}
        >
            <Stack spacing={2}>
                <Typography
                    id="threat-intelligence-details-title"
                    variant="h6"
                >
                    Threat Intelligence Details
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {threat
                        ? threat.title
                        : "Select a threat to review its details."}
                </Typography>

                <Divider />

                {detailSections.map(([section, content]) => (
                    <Stack key={section} spacing={0.5}>
                        <Typography variant="subtitle2">
                            {section}
                        </Typography>

                        <Typography
                            variant="body2"
                            color="text.secondary"
                        >
                            {content}
                        </Typography>
                    </Stack>
                ))}
            </Stack>
        </Panel>
    );
}
