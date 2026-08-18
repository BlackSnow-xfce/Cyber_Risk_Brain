import { useEffect, useRef, useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { FindingThreatIntelligenceEnrichment } from "@/workspaces/threat-intelligence/ThreatIntelligence";
import {
    getFindingThreatIntelligence,
    ThreatIntelligenceRequestError,
} from "@/workspaces/threat-intelligence/ThreatIntelligenceApiClient";

import FindingDetailsPanel from "./FindingDetailsPanel";
import type { FindingExplanationResult } from "./FindingExplanation";
import type { FindingSummary } from "./FindingSummary";
import {
    FindingExplanationRequestError,
    generateFindingExplanation,
    getFindings,
} from "./FindingsApiClient";
import FindingsList from "./FindingsList";
import FindingsToolbar from "./FindingsToolbar";

interface FindingsWorkspaceProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadExplanation?: (findingId: string) => Promise<FindingExplanationResult>;
    loadThreatIntelligence?: (
        findingId: string,
    ) => Promise<FindingThreatIntelligenceEnrichment>;
}

export default function FindingsWorkspace({
    loadFindings = getFindings,
    loadExplanation = generateFindingExplanation,
    loadThreatIntelligence = getFindingThreatIntelligence,
}: FindingsWorkspaceProps) {
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [selectedFinding, setSelectedFinding] =
        useState<FindingSummary | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [explanation, setExplanation] =
        useState<FindingExplanationResult | null>(null);
    const [explanationError, setExplanationError] = useState<string | null>(null);
    const [explanationLoading, setExplanationLoading] = useState(false);
    const explanationRequestVersion = useRef(0);
    const [threatIntelligence, setThreatIntelligence] =
        useState<FindingThreatIntelligenceEnrichment | null>(null);
    const [threatIntelligenceError, setThreatIntelligenceError] =
        useState<string | null>(null);
    const [threatIntelligenceLoading, setThreatIntelligenceLoading] =
        useState(false);
    const threatIntelligenceRequestVersion = useRef(0);

    useEffect(() => {
        let active = true;

        loadFindings()
            .then((loadedFindings) => {
                if (!active) {
                    return;
                }

                setFindings(loadedFindings);
                setSelectedFinding(loadedFindings[0] ?? null);
            })
            .catch(() => {
                if (active) {
                    setError("Live findings could not be loaded.");
                }
            })
            .finally(() => {
                if (active) {
                    setLoading(false);
                }
            });

        return () => {
            active = false;
            explanationRequestVersion.current += 1;
            threatIntelligenceRequestVersion.current += 1;
        };
    }, [loadFindings]);

    const selectFinding = (finding: FindingSummary) => {
        explanationRequestVersion.current += 1;
        setSelectedFinding(finding);
        setExplanation(null);
        setExplanationError(null);
        setExplanationLoading(false);
        threatIntelligenceRequestVersion.current += 1;
        setThreatIntelligence(null);
        setThreatIntelligenceError(null);
        setThreatIntelligenceLoading(false);
    };

    const requestThreatIntelligence = async () => {
        if (selectedFinding === null || threatIntelligenceLoading) {
            return;
        }

        const findingId = selectedFinding.id;
        const requestVersion = threatIntelligenceRequestVersion.current + 1;
        threatIntelligenceRequestVersion.current = requestVersion;
        setThreatIntelligence(null);
        setThreatIntelligenceError(null);
        setThreatIntelligenceLoading(true);

        try {
            const result = await loadThreatIntelligence(findingId);
            if (threatIntelligenceRequestVersion.current !== requestVersion) {
                return;
            }
            if (result.finding_id !== findingId) {
                setThreatIntelligenceError(
                    "Threat intelligence response did not match the selected finding.",
                );
                return;
            }
            setThreatIntelligence(result);
        } catch (requestError) {
            if (threatIntelligenceRequestVersion.current !== requestVersion) {
                return;
            }
            setThreatIntelligenceError(
                threatIntelligenceErrorMessage(requestError),
            );
        } finally {
            if (threatIntelligenceRequestVersion.current === requestVersion) {
                setThreatIntelligenceLoading(false);
            }
        }
    };

    const requestExplanation = async () => {
        if (selectedFinding === null || explanationLoading) {
            return;
        }

        const findingId = selectedFinding.id;
        const requestVersion = explanationRequestVersion.current + 1;
        explanationRequestVersion.current = requestVersion;
        setExplanation(null);
        setExplanationError(null);
        setExplanationLoading(true);

        try {
            const result = await loadExplanation(findingId);

            if (explanationRequestVersion.current !== requestVersion) {
                return;
            }

            if (result.finding_id !== findingId) {
                setExplanationError(
                    "Finding explanation response did not match the selected finding.",
                );
                return;
            }

            setExplanation(result);
        } catch (requestError) {
            if (explanationRequestVersion.current !== requestVersion) {
                return;
            }

            setExplanationError(explanationErrorMessage(requestError));
        } finally {
            if (explanationRequestVersion.current === requestVersion) {
                setExplanationLoading(false);
            }
        }
    };

    return (
        <Stack spacing={2}>
            <FindingsToolbar />

            {loading && (
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: "center" }}
                >
                    <CircularProgress size={20} />
                    <Typography>Loading live findings…</Typography>
                </Stack>
            )}

            {error && <Alert severity="error">{error}</Alert>}

            {!loading && !error && findings.length === 0 && (
                <Alert severity="info">No live findings are available.</Alert>
            )}

            {!loading && !error && findings.length > 0 && (
                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            xl: "minmax(0, 1.65fr) minmax(320px, 0.75fr)",
                        },
                        gap: 2,
                        alignItems: "start",
                        minWidth: 0,
                    }}
                >
                    <FindingsList
                        findings={findings}
                        selectedFindingId={selectedFinding?.id ?? null}
                        onSelect={selectFinding}
                    />
                    <FindingDetailsPanel
                        finding={selectedFinding}
                        explanation={explanation}
                        explanationError={explanationError}
                        explanationLoading={explanationLoading}
                        onGenerateExplanation={requestExplanation}
                        threatIntelligence={threatIntelligence}
                        threatIntelligenceError={threatIntelligenceError}
                        threatIntelligenceLoading={threatIntelligenceLoading}
                        onLoadThreatIntelligence={requestThreatIntelligence}
                    />
                </Box>
            )}
        </Stack>
    );
}

function threatIntelligenceErrorMessage(error: unknown): string {
    if (error instanceof ThreatIntelligenceRequestError) {
        if (error.status === 404) {
            return "The selected finding is no longer available.";
        }
        if (error.status === 502 || error.status === 503 || error.status === 504) {
            return "Threat intelligence sources are currently unavailable.";
        }
        if (error.status === null) {
            return "Threat intelligence request could not reach the service.";
        }
    }
    return "Threat intelligence could not be loaded for this finding.";
}

function explanationErrorMessage(error: unknown): string {
    if (error instanceof FindingExplanationRequestError) {
        if (error.status === 404) {
            return "The selected finding is no longer available.";
        }
        if (error.status === 503) {
            return "Finding explanation service is temporarily unavailable.";
        }
        if (error.status === null) {
            return "Finding explanation request could not reach the service.";
        }
    }

    return "Finding explanation could not be generated.";
}
