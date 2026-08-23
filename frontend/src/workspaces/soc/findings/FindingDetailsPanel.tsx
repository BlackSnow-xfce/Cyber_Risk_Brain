import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";
import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";

import type { FindingExplanationResult } from "./FindingExplanation";
import FindingExplanationSection from "./FindingExplanationSection";
import type { FindingIncidentReference } from "./FindingIncidentApiClient";
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
    incidents: readonly FindingIncidentReference[];
    incidentsError: string | null;
    incidentsLoading: boolean;
    onLoadIncidents: () => void;
    feedbackActive?: boolean;
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
    incidents,
    incidentsError,
    incidentsLoading,
    onLoadIncidents,
    feedbackActive = false,
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
            className={feedbackActive ? "finding-details-panel--updated" : undefined}
            sx={{
                height: "100%",
                ...(feedbackActive && {
                    animation: "finding-details-panel-update 2000ms cubic-bezier(.4, 0, .2, 1)",
                    "@keyframes finding-details-panel-update": {
                        "0%": { backgroundColor: "background.paper", borderColor: "divider", boxShadow: 0, animationTimingFunction: "cubic-bezier(.22, 1, .36, 1)" },
                        "15%": { backgroundColor: "rgba(58, 108, 157, .78)", borderColor: "rgba(121, 196, 255, .76)", boxShadow: "0 0 0 3px rgba(121, 196, 255, .46), 0 0 24px rgba(85, 168, 255, .3)", animationTimingFunction: "linear" },
                        "32.5%": { backgroundColor: "rgba(43, 84, 126, .78)", borderColor: "rgba(121, 196, 255, .6)", boxShadow: "0 0 0 2px rgba(121, 196, 255, .32), 0 0 18px rgba(85, 168, 255, .21)", animationTimingFunction: "cubic-bezier(.4, 0, .2, 1)" },
                        "100%": { backgroundColor: "background.paper", borderColor: "divider", boxShadow: 0 },
                    },
                    "@media (prefers-reduced-motion: reduce)": {
                        animation: "none",
                        backgroundColor: "rgba(58, 108, 157, .78)",
                        borderColor: "rgba(121, 196, 255, .76)",
                        boxShadow: "0 0 0 3px rgba(121, 196, 255, .46)",
                    },
                }),
            }}
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
                        <Stack spacing={1}>
                            <Divider />
                            <Stack
                                direction="row"
                                sx={{ justifyContent: "space-between", alignItems: "center" }}
                            >
                                <Typography variant="h6">Linked Incidents</Typography>
                                <Button
                                    size="small"
                                    variant="outlined"
                                    onClick={onLoadIncidents}
                                    disabled={incidentsLoading}
                                >
                                    {incidentsLoading ? "Loading…" : "Load incidents"}
                                </Button>
                            </Stack>
                            {incidentsError && <Alert severity="error">{incidentsError}</Alert>}
                            {!incidentsLoading && !incidentsError && incidents.length === 0 && (
                                <Typography variant="body2" color="text.secondary">
                                    No linked incidents loaded.
                                </Typography>
                            )}
                            {incidents.map((incident) => (
                                <Button
                                    key={incident.relationship_id}
                                    variant="text"
                                    sx={{ justifyContent: "flex-start", textTransform: "none" }}
                                    component="a"
                                    href={`/incident-response/incidents/${encodeURIComponent(incident.incident_id)}/command-center`}
                                >
                                    {incident.incident_id} · {incident.relationship_role}
                                </Button>
                            ))}
                            {incidentsLoading && <CircularProgress size={18} />}
                        </Stack>
                    </>
                )}
            </Stack>
        </Panel>
    );
}
