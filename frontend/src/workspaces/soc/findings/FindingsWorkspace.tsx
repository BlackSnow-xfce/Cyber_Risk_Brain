import { useCallback, useEffect, useMemo, useRef, useState } from "react";

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
import {
    getFindingIncidents,
    type FindingIncidentReference,
    FindingIncidentRequestError,
} from "./FindingIncidentApiClient";

interface FindingsWorkspaceProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadExplanation?: (findingId: string) => Promise<FindingExplanationResult>;
    loadThreatIntelligence?: (
        findingId: string,
    ) => Promise<FindingThreatIntelligenceEnrichment>;
    loadFindingIncidents?: (
        findingId: string,
    ) => Promise<readonly FindingIncidentReference[]>;
}

export default function FindingsWorkspace({
    loadFindings = getFindings,
    loadExplanation = generateFindingExplanation,
    loadThreatIntelligence = getFindingThreatIntelligence,
    loadFindingIncidents = getFindingIncidents,
}: FindingsWorkspaceProps) {
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
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
    const [refreshing, setRefreshing] = useState(false);
    const [findingIncidents, setFindingIncidents] = useState<readonly FindingIncidentReference[]>([]);
    const [findingIncidentsError, setFindingIncidentsError] = useState<string | null>(null);
    const [findingIncidentsLoading, setFindingIncidentsLoading] = useState(false);
    const findingIncidentsRequestVersion = useRef(0);
    const [detailFeedbackActive, setDetailFeedbackActive] = useState(false);
    const detailFeedbackTimer = useRef<number | null>(null);
    const loadThreatIntelligenceRef = useRef(loadThreatIntelligence);
    loadThreatIntelligenceRef.current = loadThreatIntelligence;
    const autoFocusRequest = useRef<string | null>(null);

    const resetFindingDetails = useCallback(() => {
        explanationRequestVersion.current += 1;
        setExplanation(null);
        setExplanationError(null);
        setExplanationLoading(false);
        threatIntelligenceRequestVersion.current += 1;
        setThreatIntelligence(null);
        setThreatIntelligenceError(null);
        setThreatIntelligenceLoading(false);
        findingIncidentsRequestVersion.current += 1;
        setFindingIncidents([]);
        setFindingIncidentsError(null);
        setFindingIncidentsLoading(false);
        autoFocusRequest.current = null;
    }, []);

    const selectLoadedFinding = useCallback((findingId: string | null) => {
        resetFindingDetails();
        setSelectedFinding(
            findings.find((finding) => finding.id === findingId) ?? null,
        );
    }, [findings, resetFindingDetails]);

    const triggerDetailFeedback = () => {
        setDetailFeedbackActive(false);
        window.requestAnimationFrame(() => setDetailFeedbackActive(true));
        if (detailFeedbackTimer.current !== null) {
            window.clearTimeout(detailFeedbackTimer.current);
        }
        detailFeedbackTimer.current = window.setTimeout(() => {
            setDetailFeedbackActive(false);
            detailFeedbackTimer.current = null;
        }, 2050);
    };

    useEffect(() => () => {
        if (detailFeedbackTimer.current !== null) {
            window.clearTimeout(detailFeedbackTimer.current);
        }
    }, []);

    const loadLiveFindings = () => {
        setLoading(true);
        setError(null);

        return loadFindings()
            .then((loadedFindings) => {
                setFindings(loadedFindings);
                const requestedFindingId = new URLSearchParams(
                    window.location.search,
                ).get("findingId");
                const requestedFinding = loadedFindings.find(
                    (finding) => finding.id === requestedFindingId,
                ) ?? null;
                resetFindingDetails();
                setSelectedFinding(requestedFinding);
                if (requestedFinding !== null) {
                    triggerDetailFeedback();
                }
            })
            .catch(() => {
                setError("Live findings could not be loaded.");
            })
            .finally(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        void loadLiveFindings();

        return () => {
            explanationRequestVersion.current += 1;
            threatIntelligenceRequestVersion.current += 1;
        };
    }, [loadFindings]);

    useEffect(() => {
        const restoreUrlSelection = () => {
            selectLoadedFinding(
                new URLSearchParams(window.location.search).get("findingId"),
            );
        };
        window.addEventListener("popstate", restoreUrlSelection);
        return () => window.removeEventListener("popstate", restoreUrlSelection);
    }, [selectLoadedFinding]);

    const filteredFindings = useMemo(() => {
        const query = searchQuery.trim().toLocaleLowerCase();
        if (!query) {
            return findings;
        }

        return findings.filter((finding) =>
            [finding.id, finding.source, finding.title, finding.vendorSeverity, finding.asset]
                .some((field) => field.toLocaleLowerCase().includes(query)),
        );
    }, [findings, searchQuery]);

    const refreshFindings = () => {
        if (refreshing) {
            return;
        }
        setRefreshing(true);
        void loadLiveFindings().finally(() => setRefreshing(false));
    };

    const selectFinding = (finding: FindingSummary) => {
        const query = new URLSearchParams();
        query.set("findingId", finding.id);
        window.history.pushState({}, "", `/findings?${query.toString()}`);
        window.dispatchEvent(new PopStateEvent("popstate"));
        triggerDetailFeedback();
    };

    const requestFindingIncidents = async () => {
        if (selectedFinding === null || findingIncidentsLoading) {
            return;
        }

        const requestVersion = findingIncidentsRequestVersion.current + 1;
        findingIncidentsRequestVersion.current = requestVersion;
        setFindingIncidentsLoading(true);
        setFindingIncidentsError(null);
        try {
            const result = await loadFindingIncidents(selectedFinding.id);
            if (findingIncidentsRequestVersion.current === requestVersion) {
                setFindingIncidents(result);
            }
        } catch (requestError) {
            if (findingIncidentsRequestVersion.current !== requestVersion) {
                return;
            }
            if (requestError instanceof FindingIncidentRequestError && requestError.status === null) {
                setFindingIncidentsError("Finding incidents could not reach the service.");
            } else {
                setFindingIncidentsError("Finding incidents could not be loaded.");
            }
        } finally {
            if (findingIncidentsRequestVersion.current === requestVersion) {
                setFindingIncidentsLoading(false);
            }
        }
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
            const result = await loadThreatIntelligenceRef.current(findingId);
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
            triggerDetailFeedback();
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

    useEffect(() => {
        const focus = new URLSearchParams(window.location.search).get("focus");
        if (
            focus !== "threat-intelligence"
            || selectedFinding === null
            || autoFocusRequest.current === selectedFinding.id
        ) {
            return;
        }

        autoFocusRequest.current = selectedFinding.id;
        void requestThreatIntelligence();
    }, [selectedFinding]);

    useEffect(() => {
        const focus = new URLSearchParams(window.location.search).get("focus");
        if (focus !== "threat-intelligence" || threatIntelligence === null) {
            return;
        }
        document.getElementById("finding-threat-intelligence")?.focus();
    }, [threatIntelligence]);

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
            <FindingsToolbar
                searchValue={searchQuery}
                onSearchChange={setSearchQuery}
                onRefresh={refreshFindings}
                refreshing={refreshing}
            />

            {loading && (
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{ alignItems: "center" }}
                >
                    <CircularProgress size={20} />
                    <Typography>Loading live findings</Typography>
                </Stack>
            )}

            {error && <Alert severity="error">{error}</Alert>}

            {!loading && !error && findings.length === 0 && (
                <Alert severity="info">No live findings are available.</Alert>
            )}

            {!loading && !error && findings.length > 0 && filteredFindings.length === 0 && (
                <Alert severity="info">No findings match the current search.</Alert>
            )}

            {!loading && !error && filteredFindings.length > 0 && (
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
                        findings={filteredFindings}
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
                        incidents={findingIncidents}
                        incidentsError={findingIncidentsError}
                        incidentsLoading={findingIncidentsLoading}
                        onLoadIncidents={requestFindingIncidents}
                        feedbackActive={detailFeedbackActive}
                    />
                </Box>
            )}
        </Stack>
    );
}

function threatIntelligenceErrorMessage(error: unknown): string {
    if (error instanceof ThreatIntelligenceRequestError) {
        if (error.status === 404) {
            return "Threat intelligence is not available for this finding.";
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
            return "Finding explanation is not available for this finding.";
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
