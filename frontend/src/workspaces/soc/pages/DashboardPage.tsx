import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Paper from "@mui/material/Paper";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";
import type { IncidentCommandCenterResponse, IncidentReference } from "@/workspaces/incident-response/IncidentCommandCenter";
import { getIncidentCommandCenter } from "@/workspaces/incident-response/IncidentCommandCenterApiClient";

import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";
import { getFindingIncidents, type FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import { getFindings } from "../findings/FindingsApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

interface DashboardPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadFindingIncidents?: (findingId: string) => Promise<readonly FindingIncidentReference[]>;
    loadIncident?: (incidentId: string) => Promise<IncidentCommandCenterResponse>;
}

type LoadState = "loading" | "ready" | "error";

export default function DashboardPage({
    loadFindings = getFindings,
    loadFindingIncidents = getFindingIncidents,
    loadIncident = getIncidentCommandCenter,
}: DashboardPageProps) {
    const location = useLocation();
    const navigate = useNavigate();
    const workspaceContext = useContext(WorkspaceContext);
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [findingsState, setFindingsState] = useState<LoadState>("loading");
    const [incidents, setIncidents] = useState<readonly FindingIncidentReference[]>([]);
    const [incidentState, setIncidentState] = useState<LoadState>("ready");
    const [commandCenter, setCommandCenter] = useState<IncidentCommandCenterResponse | null>(null);
    const [commandCenterState, setCommandCenterState] = useState<LoadState>("ready");
    const [refreshToken, setRefreshToken] = useState(0);
    const loaders = useRef({ loadFindings, loadFindingIncidents, loadIncident });
    loaders.current = { loadFindings, loadFindingIncidents, loadIncident };

    const requestedFindingId = useMemo(
        () => new URLSearchParams(location.search).get("findingId"),
        [location.search],
    );
    const finding = useMemo(
        () => findings.find(({ id }) => id === requestedFindingId) ?? null,
        [findings, requestedFindingId],
    );

    useEffect(() => {
        let current = true;
        setFindingsState("loading");
        setFindings([]);
        void loaders.current.loadFindings()
            .then((result) => {
                if (current) {
                    setFindings(result);
                    setFindingsState("ready");
                }
            })
            .catch(() => {
                if (current) setFindingsState("error");
            });
        return () => { current = false; };
    }, [refreshToken]);

    useEffect(() => {
        let current = true;
        setIncidents([]);
        setCommandCenter(null);
        setCommandCenterState("ready");
        if (findingsState !== "ready" || !finding) {
            setIncidentState("ready");
            return () => { current = false; };
        }
        setIncidentState("loading");
        void loaders.current.loadFindingIncidents(finding.id)
            .then((result) => {
                if (current) {
                    setIncidents(result);
                    setIncidentState("ready");
                }
            })
            .catch(() => {
                if (current) setIncidentState("error");
            });
        return () => { current = false; };
    }, [finding, findingsState, refreshToken]);

    const linkedIncident = incidents[0] ?? null;
    useEffect(() => {
        let current = true;
        setCommandCenter(null);
        if (incidentState !== "ready" || !linkedIncident) {
            setCommandCenterState("ready");
            return () => { current = false; };
        }
        setCommandCenterState("loading");
        void loaders.current.loadIncident(linkedIncident.incident_id)
            .then((result) => {
                if (current && result.incident.incident_id === linkedIncident.incident_id) {
                    setCommandCenter(result);
                    setCommandCenterState("ready");
                } else if (current) {
                    setCommandCenterState("error");
                }
            })
            .catch(() => {
                if (current) setCommandCenterState("error");
            });
        return () => { current = false; };
    }, [incidentState, linkedIncident]);

    const openFindings = (findingId?: string, threatIntelligence = false) => {
        workspaceContext?.setWorkspace(WorkspaceId.DECISION_CENTER);
        const query = findingId
            ? `?findingId=${encodeURIComponent(findingId)}${threatIntelligence ? "&focus=threat-intelligence" : ""}`
            : "";
        navigate(`/findings${query}`);
    };

    const openIncidentResponse = () => {
        workspaceContext?.setWorkspace(WorkspaceId.INCIDENT_RESPONSE);
        navigate("/incident-response");
    };

    const openCommandCenter = (incidentId: string) => {
        workspaceContext?.setWorkspace(WorkspaceId.INCIDENT_RESPONSE);
        navigate(`/incident-response/incidents/${encodeURIComponent(incidentId)}/command-center`);
    };

    const toolbar = <SOCWorkspaceToolbar
        onRefresh={() => setRefreshToken((value) => value + 1)}
        refreshing={[findingsState, incidentState, commandCenterState].includes("loading")}
        compact
    />;

    if (findingsState === "loading") return <DashboardMessage toolbar={toolbar} progress title="Loading SOC dashboard" detail="Retrieving canonical findings." />;
    if (findingsState === "error") return <DashboardMessage toolbar={toolbar} severity="error" title="SOC dashboard unavailable" detail="Live findings could not be loaded." />;
    if (!finding) {
        const detail = requestedFindingId
            ? "The requested findingId does not match a loaded canonical finding."
            : findings.length === 0 ? "No live findings available." : "Select a finding to open an investigation dashboard.";
        return <DashboardMessage toolbar={toolbar} title="No active investigation" detail={detail} action={<Button variant="contained" onClick={() => openFindings()}>Open Findings</Button>} />;
    }

    return (
        <Stack component="main" aria-label="Analyst workspace" spacing={1.25}>
            <Paper component="header" variant="outlined" sx={{ p: 1.5 }}>
                <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ justifyContent: "space-between" }}>
                    <Box>
                        <Typography variant="overline" color="primary.main">Active investigation</Typography>
                        <Typography variant="h5">{finding.title}</Typography>
                        <Stack direction="row" spacing={0.75} sx={{ mt: 0.75, flexWrap: "wrap" }}>
                            <Chip size="small" label={finding.id} variant="outlined" />
                            <Chip size="small" label={finding.source} variant="outlined" />
                            <Chip size="small" label={finding.vendorSeverity} color="warning" />
                            <Chip size="small" label={finding.asset} variant="outlined" />
                        </Stack>
                    </Box>
                    {toolbar}
                </Stack>
            </Paper>

            <Stack component="section" aria-label="Operational status" direction={{ xs: "column", md: "row" }} spacing={1}>
                <Status label="Finding" value="Loaded" />
                <Status label="Incident relationship" value={incidentState === "loading" ? "Loading" : incidentState === "error" ? "Unavailable" : linkedIncident?.lifecycle_status ?? "Not linked"} />
                <Status label="Command Center" value={commandCenterState === "loading" ? "Loading" : commandCenterState === "error" ? "Unavailable" : commandCenter ? commandCenter.incident.lifecycle_status : "Not available"} />
            </Stack>

            {incidentState === "error" && <Alert severity="error">Finding-to-Incident context could not be loaded.</Alert>}
            {commandCenterState === "error" && <Alert severity="error">Incident Command Center context could not be loaded.</Alert>}

            <Paper component="section" aria-label="Investigation relationship" variant="outlined" sx={{ p: 1.5 }}>
                <Typography variant="overline" color="primary.main">Relationship view</Typography>
                <Typography variant="h6">Directed investigation chain</Typography>
                <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ mt: 1, alignItems: { md: "center" } }}>
                    <Node label="Finding" primary={finding.title} secondary={finding.id} />
                    {linkedIncident && <><Typography aria-hidden="true">→</Typography><Node label={linkedIncident.relationship_role} primary={linkedIncident.incident_id} secondary={linkedIncident.lifecycle_status} /></>}
                </Stack>
            </Paper>

            <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "repeat(3, minmax(0, 1fr))" }, gap: 1 }}>
                <WorkspacePanel title="Evidence"><References references={commandCenter?.evidence ?? []} unavailable="No persisted evidence references are available." /></WorkspacePanel>
                <WorkspacePanel title="Analysis"><Typography color="text.secondary">Authoritative analysis is unavailable.</Typography></WorkspacePanel>
                <WorkspacePanel title="Recommended Investigation">
                    <Stack spacing={0.75} sx={{ alignItems: "flex-start" }}>
                        <Button onClick={() => openFindings(finding.id)}>Open Finding</Button>
                        <Button onClick={() => openFindings(finding.id, true)}>Open Threat Intelligence</Button>
                        {linkedIncident && <Button onClick={openIncidentResponse}>Open Incident</Button>}
                    </Stack>
                </WorkspacePanel>
            </Box>

            <Paper component="section" aria-label="Chronological timeline" variant="outlined" sx={{ p: 1.5 }}>
                <Typography variant="h6">Chronological timeline</Typography>
                {commandCenter?.activities.length ? <Stack component="ol" spacing={0.75} sx={{ pl: 2.5 }}>
                    {commandCenter.activities.map((activity) => <Box component="li" key={activity.activity_id}><Typography variant="body2">{activity.occurred_at} — {activity.description}</Typography><Typography variant="caption" color="text.secondary">{activity.activity_type} · {activity.activity_id}</Typography></Box>)}
                </Stack> : <Typography color="text.secondary" sx={{ mt: 0.5 }}>No canonical incident activities are available.</Typography>}
            </Paper>

            {linkedIncident && <Paper component="section" variant="outlined" sx={{ p: 1.5 }}>
                <Typography variant="overline" color="primary.main">Incident Command Center</Typography>
                {commandCenter
                    ? <><Typography variant="h6">{commandCenter.incident.title}</Typography>{commandCenter.incident.description && <Typography>{commandCenter.incident.description}</Typography>}<Typography variant="caption" color="text.secondary">Created {commandCenter.incident.created_at} · Updated {commandCenter.incident.updated_at}</Typography></>
                    : <Typography variant="body2" color="text.secondary">Canonical incident details are not available in this dashboard.</Typography>}
                <Box sx={{ mt: 1 }}><Button variant="contained" onClick={() => openCommandCenter(linkedIncident.incident_id)}>Open Command Center</Button></Box>
            </Paper>}
        </Stack>
    );
}

function DashboardMessage({ toolbar, title, detail, action, progress = false, severity = "info" }: { toolbar: ReactNode; title: string; detail: string; action?: ReactNode; progress?: boolean; severity?: "info" | "error" }) {
    return <Stack component="main" aria-label="Analyst workspace" spacing={1.25}>{toolbar}<Alert severity={severity} icon={progress ? <CircularProgress size={20} /> : undefined}><Typography sx={{ fontWeight: 700 }}>{title}</Typography><Typography variant="body2">{detail}</Typography>{action && <Box sx={{ mt: 1 }}>{action}</Box>}</Alert></Stack>;
}

function Status({ label, value }: { label: string; value: string }) {
    return <Paper variant="outlined" sx={{ p: 1, flex: 1 }}><Typography variant="caption" color="text.secondary">{label}</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{value}</Typography></Paper>;
}

function Node({ label, primary, secondary }: { label: string; primary: string; secondary: string }) {
    return <Paper variant="outlined" sx={{ p: 1, minWidth: 220 }}><Typography variant="caption" color="primary.main">{label}</Typography><Typography variant="body2" sx={{ fontWeight: 700 }}>{primary}</Typography><Typography variant="caption" color="text.secondary">{secondary}</Typography></Paper>;
}

function WorkspacePanel({ title, children }: { title: string; children: ReactNode }) {
    return <Paper component="section" variant="outlined" sx={{ p: 1.5 }}><Typography variant="h6" sx={{ mb: 0.75 }}>{title}</Typography>{children}</Paper>;
}

function References({ references, unavailable }: { references: readonly IncidentReference[]; unavailable: string }) {
    if (!references.length) return <Typography color="text.secondary">{unavailable}</Typography>;
    return <Stack component="ul" sx={{ pl: 2 }}>{references.map((reference) => <Typography component="li" variant="body2" key={reference.reference_id}>{reference.reference_id}{reference.source ? ` · ${reference.source}` : ""}</Typography>)}</Stack>;
}
