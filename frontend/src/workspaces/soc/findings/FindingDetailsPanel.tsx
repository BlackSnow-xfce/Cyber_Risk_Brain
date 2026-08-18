import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";
import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";

import type { FindingExplanationResult } from "./FindingExplanation";
import FindingExplanationSection from "./FindingExplanationSection";
import type { FindingSummary } from "./FindingSummary";
import FindingThreatIntelligenceSection from "./FindingThreatIntelligenceSection";

interface FindingDetailsPanelProps {
    finding: FindingSummary | null;
    explanation: FindingExplanationResult | null;
    explanationError: string | null;
    explanationLoading: boolean;
    onGenerateExplanation: () => void;
    threatIntelligence: FindingThreatIntelligenceEnrichment | null;
    threatIntelligenceError: string | null;
    threatIntelligenceLoading: boolean;
    onLoadThreatIntelligence: () => void;
}

export default function FindingDetailsPanel({
    finding,
    explanation,
    explanationError,
    explanationLoading,
    onGenerateExplanation,
    threatIntelligence,
    threatIntelligenceError,
    threatIntelligenceLoading,
    onLoadThreatIntelligence,
}: FindingDetailsPanelProps) {
    const detailSections = finding
        ? [
              ["Source ID", finding.id],
              ["Source", finding.source],
              ["Vendor Severity", finding.vendorSeverity],
              ["Asset", finding.asset],
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

                {finding && (
                    <Typography variant="body2" color="text.secondary">
                        Canonical scanner finding. Risk and decision enrichment
                        is not available for this live data.
                    </Typography>
                )}

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

                {finding && (
                    <>
                        <FindingThreatIntelligenceSection
                            result={threatIntelligence}
                            error={threatIntelligenceError}
                            loading={threatIntelligenceLoading}
                            onLoad={onLoadThreatIntelligence}
                        />
                        <FindingExplanationSection
                            explanation={explanation}
                            error={explanationError}
                            loading={explanationLoading}
                            onGenerate={onGenerateExplanation}
                        />
                    </>
                )}
            </Stack>
        </Panel>
    );
}
