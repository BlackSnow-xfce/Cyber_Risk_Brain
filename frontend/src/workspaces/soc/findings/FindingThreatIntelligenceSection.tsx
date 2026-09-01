import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";
import ThreatIntelligenceResult from "@/workspaces/threat-intelligence/pages/ThreatIntelligenceResult";

import { findingsDensity } from "./FindingsPresentationDensity";

interface FindingThreatIntelligenceSectionProps {
    result: FindingThreatIntelligenceEnrichment | null;
    error: string | null;
    loading: boolean;
    onLoad: () => void;
}

export default function FindingThreatIntelligenceSection({
    result,
    error,
    loading,
    onLoad,
}: FindingThreatIntelligenceSectionProps) {
    return (
        <Stack
            component="section"
            spacing={2}
            sx={{ "& .MuiChip-root": findingsDensity.chip }}
            aria-label="Finding threat intelligence"
            id="finding-threat-intelligence"
            tabIndex={-1}
        >
            <Divider />
            <Stack spacing={0.5}>
                <Typography variant="subtitle2" sx={findingsDensity.sectionHeading} data-ti-density-role="section-heading">Threat Intelligence</Typography>
                <Typography variant="body2" color="text.secondary" sx={findingsDensity.helpText}>
                    Load CVE-based intelligence supplied by the PredatorAI backend
                    for this finding.
                </Typography>
            </Stack>

            <Button variant="outlined" onClick={onLoad} disabled={loading} sx={findingsDensity.toolbarButton}>
                {loading ? "Loading" : "Load Threat Intelligence"}
            </Button>

            {loading && (
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <CircularProgress size={20} />
                    <Typography sx={findingsDensity.helpText}>Loading finding threat intelligence</Typography>
                </Stack>
            )}

            {error && <Alert severity="error">{error}</Alert>}

            {result && (
                <Stack spacing={2}>
                    <Stack spacing={0.5}>
                        <Typography variant="subtitle2" sx={findingsDensity.subsectionHeading}>Finding context</Typography>
                        <Typography variant="body2" sx={findingsDensity.primaryValue}>ID: {result.finding_id}</Typography>
                        <Typography variant="body2" sx={findingsDensity.primaryValue}>Title: {result.finding_title}</Typography>
                        <Typography variant="body2" sx={findingsDensity.primaryValue}>Source: {result.finding_source}</Typography>
                    </Stack>

                    {result.relationships.map((relationship) => {
                        const relationshipKey =
                            relationship.cve_identifier ?? relationship.applicability;

                        if (relationship.intelligence === null) {
                            return (
                                <Alert key={relationshipKey} severity="info">
                                    Applicability: {relationship.applicability}. No
                                    applicable CVE-based threat intelligence is
                                    available for this finding.
                                </Alert>
                            );
                        }

                        return (
                            <Stack key={relationshipKey} spacing={1.5}>
                                <Typography variant="subtitle2" sx={findingsDensity.subsectionHeading}>
                                    Applicability: {relationship.applicability}
                                </Typography>
                                <ThreatIntelligenceResult
                                    intelligence={relationship.intelligence}
                                    presentationDensity={findingsDensity}
                                />
                            </Stack>
                        );
                    })}
                </Stack>
            )}
        </Stack>
    );
}
