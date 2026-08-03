import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { Finding } from "./Finding";

interface FindingDetailsPanelProps {
    finding: Finding | null;
}

export default function FindingDetailsPanel({
    finding,
}: FindingDetailsPanelProps) {
    const detailSections = finding
        ? [
              ["Executive Summary", finding.description],
              ["Explainability", finding.explainability.reason],
              [
                  "Evidence",
                  finding.evidence
                      .map(
                          (evidence) =>
                              `${evidence.title}: ${evidence.description}`,
                      )
                      .join("; "),
              ],
              ["Recommendations", finding.recommendation.description],
          ] as const
        : [];

    return (
        <Panel
            component="aside"
            aria-labelledby="finding-details-title"
            sx={{ height: "100%" }}
        >
            <Stack spacing={2}>
                <Typography
                    id="finding-details-title"
                    variant="h6"
                >
                    Finding Details
                </Typography>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    {finding
                        ? finding.title
                        : "Select a finding to review its details."}
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
