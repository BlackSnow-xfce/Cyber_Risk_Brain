import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Investigation } from "./Investigation";

interface InvestigationDetailsPanelProps {
    investigation: Investigation | null;
}

export default function InvestigationDetailsPanel({
    investigation,
}: InvestigationDetailsPanelProps) {
    const detailSections = investigation
        ? [
              ["Executive Summary", investigation.description],
              ["Timeline", investigation.timeline],
              ["Related Findings", investigation.relatedFindings],
              [
                  "Evidence",
                  investigation.evidence
                      .map(
                          (evidence) =>
                              `${evidence.title}: ${evidence.description}`,
                      )
                      .join("; "),
              ],
              ["Analyst Notes", investigation.analystNotes],
              [
                  "Recommended Actions",
                  investigation.recommendation.description,
              ],
          ] as const
        : [];

    return (
        <Panel
            component="aside"
            aria-labelledby="investigation-details-title"
            sx={{ height: "100%" }}
        >
            <Stack spacing={2}>
                <Typography
                    id="investigation-details-title"
                    variant="h6"
                >
                    Investigation Details
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {investigation
                        ? investigation.title
                        : "Select an investigation to review its details."}
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
