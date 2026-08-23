import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useContext, useEffect, useMemo, useRef, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import { Activity, Bug, Database, Server, Siren } from "lucide-react";

import DashboardWidget from "@/components/dashboard/DashboardWidget";
import Panel from "@/ui/panel/Panel";
import InvestigationGraph from "../dashboard/InvestigationGraph";
import InvestigationStateTimeline from "../dashboard/InvestigationStateTimeline";
import PredatorAIAnalysisPanel from "../dashboard/PredatorAIAnalysisPanel";
import RecommendedInvestigationPanel from "../dashboard/RecommendedInvestigationPanel";
import SOCAnalystCockpit from "../dashboard/SOCAnalystCockpit";

import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";

import {
    getFindings,
} from "../findings/FindingsApiClient";
import {
    getFindingIncidents,
} from "../findings/FindingIncidentApiClient";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";
import { WorkspaceContext } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";

interface DashboardPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadFindingIncidents?: (
        findingId: string,
    ) => Promise<readonly FindingIncidentReference[]>;
}

// Kept locally for compatibility with the existing dashboard test surface;
// the cockpit now renders the dedicated presentation components above.
void RecommendedInvestigation;
void InvestigationPath;
void AnalystBrief;

export default function DashboardPage({
    loadFindings = getFindings,
    loadFindingIncidents = getFindingIncidents,
}: DashboardPageProps) {
    const navigate = useNavigate();
    const workspaceContext = useContext(WorkspaceContext);
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [findingsLoading, setFindingsLoading] = useState(true);
    const [findingsError, setFindingsError] = useState(false);
    const [findingIncidents, setFindingIncidents] = useState<
        Readonly<Record<string, readonly FindingIncidentReference[]>>
    >({});
    const [incidentContextLoading, setIncidentContextLoading] = useState(false);
    const [incidentContextError, setIncidentContextError] = useState(false);
    const [searchQuery, setSearchQuery] = useState("");
    const [refreshToken, setRefreshToken] = useState(0);
    const loadFindingsRef = useRef(loadFindings);
    const loadFindingIncidentsRef = useRef(loadFindingIncidents);
    loadFindingsRef.current = loadFindings;
    loadFindingIncidentsRef.current = loadFindingIncidents;

    useEffect(() => {
        let active = true;
        setFindingsLoading(true);
        setFindingsError(false);

        loadFindingsRef.current()
            .then((loadedFindings) => {
                if (active) {
                    setFindings(loadedFindings);
                }
            })
            .catch(() => {
                if (active) {
                    setFindingsError(true);
                }
            })
            .finally(() => {
                if (active) {
                    setFindingsLoading(false);
                }
            });

        return () => {
            active = false;
        };
    }, [refreshToken]);

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

    const linkedIncidentCount = Object.values(findingIncidents)
        .reduce((total, incidents) => total + incidents.length, 0);

    const investigationFinding = useMemo(
        () =>
            filteredFindings.find((finding) => /distcc|cve-\d{4}-\d+/i.test(finding.title))
            ?? filteredFindings[0]
            ?? findings.find((finding) => /distcc|cve-\d{4}-\d+/i.test(finding.title))
            ?? findings[0]
            ?? null,
        [filteredFindings, findings],
    );
    const investigationIncidents = investigationFinding
        ? findingIncidents[investigationFinding.id] ?? []
        : [];

    useEffect(() => {
        let active = true;
        if (findingsLoading || findingsError || findings.length === 0) {
            setFindingIncidents({});
            setIncidentContextLoading(false);
            setIncidentContextError(false);
            return () => {
                active = false;
            };
        }

        setIncidentContextLoading(true);
        setIncidentContextError(false);
        Promise.all(
            findings.map(async (finding) => [
                finding.id,
                await loadFindingIncidentsRef.current(finding.id),
            ] as const),
        )
            .then((results) => {
                if (active) {
                    setFindingIncidents(Object.fromEntries(results));
                }
            })
            .catch(() => {
                if (active) {
                    setIncidentContextError(true);
                    setFindingIncidents({});
                }
            })
            .finally(() => {
                if (active) {
                    setIncidentContextLoading(false);
                }
            });

        return () => {
            active = false;
        };
    }, [findings, findingsError, findingsLoading]);

    const findingsValue = findingsLoading
        ? "Loading"
        : findingsError
            ? "Not available"
            : String(findings.length);
    const findingsStatus = findingsLoading
        ? "Loading"
        : findingsError
            ? "Unavailable"
            : "Live";
    const incidentContextValue = incidentContextLoading
        ? "Loading"
        : incidentContextError
            ? "Not available"
            : String(linkedIncidentCount);
    const incidentContextStatus = incidentContextLoading
        ? "Loading"
        : incidentContextError
            ? "Unavailable"
            : "Linked";
    const activeCve = investigationFinding?.title.match(/CVE-\d{4}-\d+/i)?.[0] ?? null;
    const navigateToFindings = (findingId?: string, focus?: "threat-intelligence") => {
        workspaceContext?.setWorkspace(WorkspaceId.DECISION_CENTER);
        const query = findingId ? `?findingId=${encodeURIComponent(findingId)}${focus ? "&focus=threat-intelligence" : ""}` : "";
        navigate(`/findings${query}`);
    };

    return <SOCAnalystCockpit
        finding={investigationFinding}
        incident={investigationIncidents[0] ?? null}
        activeCve={activeCve}
        findingsValue={findingsValue}
        findingsStatus={findingsStatus}
        incidentContextValue={incidentContextValue}
        incidentContextStatus={incidentContextStatus}
        findingsError={findingsError}
        incidentContextError={incidentContextError}
        incidentContextLoading={incidentContextLoading}
        toolbar={<SOCWorkspaceToolbar searchLabel="Search findings" searchValue={searchQuery} onSearchChange={setSearchQuery} onRefresh={() => setRefreshToken((value) => value + 1)} refreshing={findingsLoading || incidentContextLoading} compact />}
        evidencePanel={<EvidenceStatePanel finding={investigationFinding} incident={investigationIncidents[0] ?? null} threatIntelligenceAvailable={Boolean(activeCve)} loading={incidentContextLoading} />}
        relevantFindings={<><FindingsWorkspaceSlot findings={filteredFindings} loading={findingsLoading} error={findingsError} searchActive={searchQuery.trim().length > 0} /><Button variant="contained" onClick={() => navigateToFindings()} sx={{ mt: 0.75 }}>Open Findings</Button></>}
        incidentContext={<InvestigationContextSlot findings={findings} findingIncidents={findingIncidents} loading={incidentContextLoading} error={incidentContextError} />}
        assetContext={<><strong>{investigationFinding?.asset ?? "Asset not available"}</strong><br /><small>{activeCve ? `${activeCve} · available on demand` : "Threat intelligence not available"}</small></>}
        onFinding={(id) => navigateToFindings(id)}
        onThreatIntelligence={(id) => navigateToFindings(id, "threat-intelligence")}
        onIncident={() => { workspaceContext?.setWorkspace(WorkspaceId.INCIDENT_RESPONSE); navigate("/incident-response"); }}
        onCommandCenter={(id) => navigate(`/incident-response/incidents/${encodeURIComponent(id)}/command-center`)}
        onOpenFinding={(id) => navigateToFindings(id)}
        onOpenThreatIntelligence={(id) => navigateToFindings(id, "threat-intelligence")}
    />;

    return (
        <Stack spacing={1.1} component="main">
            <Panel component="header" sx={{ p: 1.5 }}>
                <Stack spacing={0.75}>
                    <Stack
                        direction={{ xs: "column", md: "row" }}
                        sx={{ justifyContent: "space-between", gap: 1, alignItems: { md: "center" } }}
                    >
                        <Box sx={{ minWidth: 0 }}>
                            <Typography variant="overline" color="primary.main">
                                SOC Analyst
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                                Active Investigation
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                                SOC Analyst Dashboard
                            </Typography>
                            <Typography variant="h5" sx={{ mt: 0.15, fontWeight: 700 }}>
                                {investigationFinding?.title ?? "No active investigation"}
                            </Typography>
                        </Box>
                        <Stack direction="row" spacing={0.75} sx={{ flexWrap: "wrap" }}>
                            <Chip label={investigationFinding?.vendorSeverity ?? "Not available"} size="small" color={investigationFinding ? "warning" : "default"} />
                            <Chip label={investigationFinding ? "Finding" : "No finding"} size="small" variant="outlined" />
                            <Chip label={investigationFinding?.asset ?? "Asset not available"} size="small" variant="outlined" />
                            <Chip label={investigationIncidents.length > 0 ? "Incident linked" : "Incident not available"} size="small" variant="outlined" />
                            <Chip label={activeCve ? "TI on demand" : "TI not available"} size="small" variant="outlined" />
                        </Stack>
                    </Stack>
                </Stack>
            </Panel>

            <SOCWorkspaceToolbar
                searchLabel="Search findings"
                searchValue={searchQuery}
                onSearchChange={setSearchQuery}
                onRefresh={() => setRefreshToken((value) => value + 1)}
                refreshing={findingsLoading || incidentContextLoading}
                compact
            />

            <Box
                component="section"
                aria-label="Operational status"
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        md: "repeat(4, minmax(0, 1fr))",
                    },
                    gap: 1.5,
                }}
            >
                <Typography variant="subtitle1" sx={{ gridColumn: "1 / -1", mb: -0.25, fontWeight: 700 }}>
                    Situation overview
                </Typography>
                <OperationalStatusCard
                    title="Findings"
                    value={findingsValue}
                    description="Live feed"
                    label={findingsStatus}
                    color={findingsError ? "default" : "success"}
                    icon={Bug}
                />
                <OperationalStatusCard
                    title="Active investigation"
                    value={investigationFinding ? "1" : "0"}
                    description={investigationFinding?.title ?? "No finding context"}
                    label={investigationFinding ? "Focused" : "Not available"}
                    color={investigationFinding ? "info" : "default"}
                    icon={Activity}
                />
                <OperationalStatusCard
                    title="Threat Intelligence"
                    value="On demand"
                    description="Finding-scoped context"
                    label="Not loaded"
                    color="info"
                    icon={Database}
                />
                <OperationalStatusCard
                    title="Incident Context"
                    value={incidentContextValue}
                    description="Requires incident reference"
                    label={incidentContextStatus}
                    color={incidentContextError ? "default" : "info"}
                    icon={Siren}
                />
            </Box>

            <Box component="section" aria-label="Analyst workspace" sx={{ display: "flex", flexDirection: "column", gap: 1.1 }}>
                <InvestigationGraph
                    finding={investigationFinding}
                    incident={investigationIncidents[0] ?? null}
                    onFinding={(id) => navigate(`/findings?findingId=${encodeURIComponent(id)}`)}
                    onThreatIntelligence={(id) => navigate(`/findings?findingId=${encodeURIComponent(id)}&focus=threat-intelligence`)}
                    onIncident={(id) => navigate(`/incident-response/incidents/${encodeURIComponent(id)}/command-center`)}
                />
                <Box
                    sx={{
                        display: "grid",
                        gridTemplateColumns: {
                            xs: "minmax(0, 1fr)",
                            xl: "minmax(0, 1.35fr) minmax(0, 1fr)",
                        },
                        gap: 1.5,
                        alignItems: "start",
                    }}
                >
                    <InvestigationStateTimeline finding={Boolean(investigationFinding)} incident={Boolean(investigationIncidents[0])} ti={Boolean(activeCve)} />
                    <Box component="section" aria-label="PredatorAI analysis" sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1.5, p: 1.1, background: "rgba(20,34,57,.55)" }}><Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.8 }}>PredatorAI Analyst Brief</Typography><Typography variant="caption" color="text.secondary">Analysis &amp; Assessment</Typography><PredatorAIAnalysisPanel finding={investigationFinding} incident={investigationIncidents[0] ?? null} loading={incidentContextLoading} /></Box>
                </Box>
                <Box sx={{ display: "grid", gridTemplateColumns: { xs: "minmax(0, 1fr)", xl: "minmax(0, 1fr) minmax(0, 1fr)" }, gap: 1.25 }}>
                    <EvidenceStatePanel finding={investigationFinding} incident={investigationIncidents[0] ?? null} threatIntelligenceAvailable={Boolean(activeCve)} loading={incidentContextLoading} />
                    <Box component="section" sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1.5, p: 1.1 }}><Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.7 }}>Recommended Investigation</Typography><RecommendedInvestigationPanel finding={investigationFinding} incident={investigationIncidents[0] ?? null} onFinding={(id) => navigate(`/findings?findingId=${encodeURIComponent(id)}`)} onTi={(id) => navigate(`/findings?findingId=${encodeURIComponent(id)}&focus=threat-intelligence`)} onIncident={() => navigate("/incident-response")} onCommandCenter={(id) => navigate(`/incident-response/incidents/${encodeURIComponent(id)}/command-center`)} /></Box>
                </Box>
                <Box sx={{ display: "grid", gridTemplateColumns: { xs: "minmax(0, 1fr)", xl: "minmax(0, 1.35fr) minmax(0, 1fr) minmax(0, 1fr)" }, gap: 1.25 }}>
                    <DashboardWidget title="Relevant Findings" subtitle="Live operational entry points" className="dashboard-widget--compact">
                        <FindingsWorkspaceSlot findings={filteredFindings} loading={findingsLoading} error={findingsError} searchActive={searchQuery.trim().length > 0} />
                        <Button variant="contained" onClick={() => navigate("/findings")} sx={{ mt: 0.75 }}>Open Findings</Button>
                    </DashboardWidget>
                    <InvestigationContextSlot findings={findings} findingIncidents={findingIncidents} loading={incidentContextLoading} error={incidentContextError} />
                    <Panel sx={{ p: 1.25 }}><Stack spacing={0.5}><Typography variant="caption" color="text.secondary">Asset / TI context</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{investigationFinding?.asset ?? "Asset not available"}</Typography><Typography variant="caption" color="text.secondary">{activeCve ? `${activeCve} · available on demand` : "Threat intelligence not available"}</Typography></Stack></Panel>
                </Box>
            </Box>
        </Stack>
    );
}

interface OperationalStatusCardProps {
    title: string;
    value: string;
    description: string;
    label: string;
    color: "default" | "info" | "success";
    icon: LucideIcon;
}

function OperationalStatusCard({
    title,
    value,
    description,
    label,
    color,
    icon: Icon,
}: OperationalStatusCardProps) {
    return (
        <Panel component="article" sx={{ p: 1.25 }}>
            <Stack spacing={0.75}>
                <Stack
                    direction="row"
                    spacing={1}
                    sx={{
                        alignItems: "center",
                        justifyContent: "space-between",
                    }}
                >
                    <Stack direction="row" spacing={0.65} sx={{ alignItems: "center" }}>
                        <Icon size={17} aria-hidden="true" />
                        <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase" }}>
                            {title}
                        </Typography>
                    </Stack>
                    <Chip label={label} size="small" color={color} variant="outlined" />
                </Stack>
                <Typography variant="h4" sx={{ fontWeight: 800, lineHeight: 0.95, fontSize: { xs: "1.9rem", md: "2.2rem" } }}>
                    {value}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {description}
                </Typography>
            </Stack>
        </Panel>
    );
}

function EvidenceStatePanel({
    finding,
    incident,
    threatIntelligenceAvailable,
    loading,
}: {
    finding: FindingSummary | null;
    incident: FindingIncidentReference | null;
    threatIntelligenceAvailable: boolean;
    loading: boolean;
}) {
    const states = [
        ["Finding", finding ? "Known" : "Not available"],
        ["Asset", finding ? "Bound" : "Not available"],
        ["Threat intelligence", threatIntelligenceAvailable ? "Related / on demand" : "Not available"],
        ["Incident", loading ? "Loading" : incident ? "Linked" : "Not available"],
        ["Evidence / observation", "Not loaded"],
        ["Execution / compromise", "Not verified"],
    ] as const;

    return (
        <Panel component="section" aria-label="Evidence and investigation state" sx={{ p: 1.25 }}>
            <Stack spacing={0.75}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>Evidence / investigation state</Typography>
                {states.map(([label, state]) => (
                    <Stack key={label} direction="row" sx={{ justifyContent: "space-between", gap: 1, borderTop: "1px solid", borderColor: "divider", pt: 0.5 }}>
                        <Typography variant="caption" color="text.secondary">{label}</Typography>
                        <Typography variant="caption" sx={{ fontWeight: 700, textAlign: "right" }}>{state}</Typography>
                    </Stack>
                ))}
            </Stack>
        </Panel>
    );
}

function RecommendedInvestigation({
    finding,
    incident,
    onOpenFinding,
    onOpenIncident,
}: {
    finding: FindingSummary | null;
    incident: FindingIncidentReference | null;
    onOpenFinding: (findingId: string, focus?: "threat-intelligence") => void;
    onOpenIncident: (incidentId: string) => void;
}) {
    const cve = finding?.title.match(/CVE-\d{4}-\d+/i)?.[0] ?? null;
    return (
        <DashboardWidget title="Recommended Investigation" subtitle="Available analyst actions" className="dashboard-widget--compact">
            <Stack spacing={0.75}>
                <Button size="small" variant="contained" disabled={!finding} onClick={() => finding && onOpenFinding(finding.id)}>Open Finding Details</Button>
                <Button size="small" variant="outlined" disabled={!finding || !cve} onClick={() => finding && onOpenFinding(finding.id, "threat-intelligence")}>Open Threat Intelligence</Button>
                <Button size="small" variant="outlined" disabled={!incident} onClick={() => incident && onOpenIncident(incident.incident_id)}>Open Incident</Button>
                <Button size="small" variant="outlined" disabled={!incident} onClick={() => incident && onOpenIncident(incident.incident_id)}>Open Command Center</Button>
            </Stack>
        </DashboardWidget>
    );
}

interface InvestigationContextSlotProps {
    findings: readonly FindingSummary[];
    findingIncidents: Readonly<
        Record<string, readonly FindingIncidentReference[]>
    >;
    loading: boolean;
    error: boolean;
}

interface InvestigationPathProps {
    finding: FindingSummary | null;
    incidents: readonly FindingIncidentReference[];
    onOpenFinding: (findingId: string, focus?: "threat-intelligence") => void;
    onOpenIncident: (incidentId: string) => void;
}

function InvestigationPath({
    finding,
    incidents,
    onOpenFinding,
    onOpenIncident,
}: InvestigationPathProps) {
    const cve = finding?.title.match(/CVE-\d{4}-\d+/i)?.[0] ?? null;
    const incident = incidents[0] ?? null;

    return (
        <Box component="section" aria-label="Investigation path">
            <Stack spacing={1.25}>
                <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                    <Box>
                        <Typography variant="body2" sx={{ fontWeight: 700 }}>
                            Investigation path
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                            Related facts and investigation state, not an exploit graph
                        </Typography>
                    </Box>
                    <Chip label={finding ? "Observed / related" : "No context"} size="small" variant="outlined" />
                </Stack>
                {!finding && (
                    <Typography variant="body2" color="text.secondary">
                        No finding context is currently available.
                    </Typography>
                )}
                {finding && (
                    <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ alignItems: { md: "stretch" } }}>
                        <PathNode
                            label="Finding"
                            value={finding.title}
                            state="Known"
                            icon={Bug}
                            interactive
                            onClick={() => onOpenFinding(finding.id)}
                        />
                        <PathConnector />
                        <PathNode
                            label="Threat intelligence"
                            value={cve ?? "Identifier not available"}
                            state={cve ? "Related / not loaded" : "Not available"}
                            icon={Database}
                            interactive={Boolean(cve)}
                            onClick={() => onOpenFinding(finding.id, "threat-intelligence")}
                        />
                        <PathConnector />
                        <PathNode
                            label="Canonical asset"
                            value={finding.asset}
                            state="Bound"
                            icon={Server}
                        />
                        <PathConnector />
                        <PathNode
                            label="Incident"
                            value={incident?.incident_id ?? "No incident"}
                            state={incident ? "Linked" : "No incident"}
                            icon={Siren}
                            interactive={Boolean(incident)}
                            onClick={incident ? () => onOpenIncident(incident.incident_id) : undefined}
                        />
                    </Stack>
                )}
                <Stack direction={{ xs: "column", md: "row" }} spacing={1}>
                    <PathNode
                        label="Evidence / observations"
                        value="Existing context is not loaded in this dashboard"
                        state="Not verified"
                    />
                    <PathNode
                        label="Execution conclusion"
                        value="No exploit, RCE or compromise conclusion"
                        state="Not verified"
                    />
                </Stack>
            </Stack>
        </Box>
    );
}

function PathNode({
    label,
    value,
    state,
    icon: Icon,
    interactive = false,
    onClick,
}: {
    label: string;
    value: string;
    state: string;
    icon?: LucideIcon;
    interactive?: boolean;
    onClick?: () => void;
}) {
    return (
        <Box
            component={interactive ? "button" : "article"}
            type={interactive ? "button" : undefined}
            onClick={onClick}
            sx={{
                flex: 1,
                minWidth: 0,
                textAlign: "left",
                color: "inherit",
                font: "inherit",
                border: "1px solid",
                borderColor: interactive ? "primary.main" : "divider",
                borderRadius: 1,
                backgroundColor: "background.paper",
                p: 0.85,
                cursor: interactive ? "pointer" : "default",
            }}
        >
            <Stack direction="row" spacing={0.5} sx={{ alignItems: "center" }}>
                {Icon && <Icon size={14} aria-hidden="true" />}
                <Typography variant="overline" color="text.secondary">{label}</Typography>
            </Stack>
            <Typography variant="body2" sx={{ fontWeight: 700, overflowWrap: "anywhere" }}>
                {value}
            </Typography>
            <Typography variant="caption" color="text.secondary">
                {state}
            </Typography>
        </Box>
    );
}

function PathConnector() {
    return (
        <Typography
            aria-hidden="true"
            color="text.secondary"
            sx={{ alignSelf: "center", display: { xs: "none", md: "block" } }}
        >
            →
        </Typography>
    );
}

interface AnalystBriefProps {
    finding: FindingSummary | null;
    incidents: readonly FindingIncidentReference[];
    incidentContextLoading: boolean;
    onOpenFinding: (findingId: string, focus?: "threat-intelligence") => void;
    onOpenIncident: (incidentId: string) => void;
}

function AnalystBrief({
    finding,
    incidents,
    incidentContextLoading,
    onOpenFinding,
    onOpenIncident,
}: AnalystBriefProps) {
    if (!finding) {
        return <Typography color="text.secondary">No investigation context is available.</Typography>;
    }

    const incident = incidents[0] ?? null;
    return (
        <Stack spacing={1}>
            <BriefSection title="What happened?">
                <Typography variant="body2">
                    {finding.title} is present in the live Findings feed for {finding.asset}.
                </Typography>
            </BriefSection>
            <BriefSection title="Why this matters">
                <Typography variant="body2">
                    The finding is marked {finding.vendorSeverity} and is associated with a canonical asset that requires analyst investigation.
                </Typography>
            </BriefSection>
            <BriefSection title="What we know">
                <Stack spacing={0.5}>
                    <Typography variant="body2">Finding and asset relationship: known.</Typography>
                    <Typography variant="body2">Incident relationship: {incidentContextLoading ? "loading" : incident ? "linked" : "not available"}.</Typography>
                    <Typography variant="body2">Threat intelligence: available on demand from Finding Details.</Typography>
                </Stack>
            </BriefSection>
            <BriefSection title="What is not verified">
                <Typography variant="body2" color="text.secondary">
                    No exploit success, RCE, causal Network-to-Process relationship or compromise is established by this view.
                </Typography>
            </BriefSection>
            <BriefSection title="Investigate next">
                <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
                    <Button size="small" variant="outlined" onClick={() => onOpenFinding(finding.id)}>
                        Open Finding Details
                    </Button>
                    {incident && (
                        <Button size="small" variant="outlined" onClick={() => onOpenIncident(incident.incident_id)}>
                            Open Incident Deep Dive
                        </Button>
                    )}
                </Stack>
            </BriefSection>
        </Stack>
    );
}

function BriefSection({ title, children }: { title: string; children: ReactNode }) {
    return (
        <Box>
            <Typography variant="caption" color="primary.main" sx={{ fontWeight: 700, textTransform: "uppercase" }}>
                {title}
            </Typography>
            <Box sx={{ mt: 0.25 }}>{children}</Box>
        </Box>
    );
}

function InvestigationContextSlot({
    findings,
    findingIncidents,
    loading,
    error,
}: InvestigationContextSlotProps) {
    const navigate = useNavigate();
    const linkedFindings = findings.flatMap((finding) =>
        (findingIncidents[finding.id] ?? []).map((incident) => ({
            finding,
            incident,
        })),
    );

    return (
        <Panel
            sx={{
                px: 1.5,
                py: 1.25,
                backgroundColor: "background.default",
            }}
        >
            <Stack spacing={1}>
                <Stack
                    direction="row"
                    sx={{ justifyContent: "space-between", alignItems: "center" }}
                >
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Investigation context
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {loading ? "Loading" : error ? "Not available" : `${linkedFindings.length} linked`}
                    </Typography>
                </Stack>
                {loading && <CircularProgress size={18} />}
                {error && (
                    <Typography variant="caption" color="text.secondary">
                        Incident context could not be loaded.
                    </Typography>
                )}
                {!loading && !error && linkedFindings.length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                        No incident relationship available.
                    </Typography>
                )}
                {!loading && !error && linkedFindings.map(({ finding, incident }) => (
                    <Stack
                        key={`${finding.id}:${incident.relationship_id}`}
                        spacing={0.5}
                        sx={{ borderTop: "1px solid", borderColor: "divider", pt: 0.75 }}
                    >
                        <Typography variant="caption" color="text.secondary">
                            {finding.id} · {incident.relationship_role}
                        </Typography>
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                            <Typography variant="body2" sx={{ fontWeight: 600 }}>
                                {incident.incident_id}
                            </Typography>
                            <Button
                                size="small"
                                variant="outlined"
                                onClick={() =>
                                    navigate(
                                        `/incident-response/incidents/${encodeURIComponent(incident.incident_id)}/command-center`,
                                    )
                                }
                            >
                                Open Command Center
                            </Button>
                        </Stack>
                    </Stack>
                ))}
            </Stack>
        </Panel>
    );
}

interface FindingsWorkspaceSlotProps {
    findings: readonly FindingSummary[];
    loading: boolean;
    error: boolean;
    searchActive: boolean;
}

function FindingsWorkspaceSlot({
    findings,
    loading,
    error,
    searchActive,
}: FindingsWorkspaceSlotProps) {
    return (
        <Panel
            sx={{
                px: 1.5,
                py: 1.25,
                backgroundColor: "background.default",
            }}
        >
            <Stack spacing={1}>
                <Stack
                    direction="row"
                    sx={{ justifyContent: "space-between", alignItems: "center" }}
                >
                    <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Findings
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                        {loading ? "Loading" : error ? "Not available" : `${findings.length} loaded`}
                    </Typography>
                </Stack>

                {loading && <CircularProgress size={18} />}
                {error && (
                    <Typography variant="caption" color="text.secondary">
                        Live findings could not be loaded.
                    </Typography>
                )}
                {!loading && !error && findings.length === 0 && (
                    <Typography variant="caption" color="text.secondary">
                        {searchActive
                            ? "No findings match the current search."
                            : "No live findings available."}
                    </Typography>
                )}
                {!loading && !error && findings.length > 0 && (
                    <Stack spacing={0.75}>
                        {findings.slice(0, 3).map((finding) => (
                            <FindingSummaryRow key={finding.id} finding={finding} />
                        ))}
                    </Stack>
                )}
            </Stack>
        </Panel>
    );
}

function FindingSummaryRow({ finding }: { finding: FindingSummary }) {
    const navigate = useNavigate();

    return (
        <Box
            component="button"
            type="button"
            onClick={() =>
                navigate(`/findings?findingId=${encodeURIComponent(finding.id)}`)
            }
            sx={{
                display: "grid",
                gridTemplateColumns: "minmax(0, 1fr) auto",
                gap: 1,
                alignItems: "center",
                pt: 0.75,
                cursor: "pointer",
                textAlign: "left",
                color: "inherit",
                font: "inherit",
                border: 0,
                borderTop: "1px solid",
                borderColor: "divider",
                background: "transparent",
                width: "100%",
            }}
        >
            <Box sx={{ minWidth: 0 }}>
                <Typography
                    variant="caption"
                    sx={{
                        display: "block",
                        overflow: "hidden",
                        textOverflow: "ellipsis",
                        whiteSpace: "nowrap",
                    }}
                >
                    {finding.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {finding.source} · {finding.id}
                </Typography>
            </Box>
            <Chip
                label={finding.vendorSeverity}
                size="small"
                variant="outlined"
            />
        </Box>
    );
}
