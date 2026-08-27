import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { WorkspaceContext } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";
import type { IncidentCommandCenterResponse, IncidentReference } from "@/workspaces/incident-response/IncidentCommandCenter";
import { getIncidentCommandCenter } from "@/workspaces/incident-response/IncidentCommandCenterApiClient";
import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";
import SOCAnalystCockpit from "../dashboard/SOCAnalystCockpit";
import { getFindingIncidents, type FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import { getFindings } from "../findings/FindingsApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

interface DashboardPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
    loadFindingIncidents?: (findingId: string) => Promise<readonly FindingIncidentReference[]>;
    loadIncident?: (incidentId: string) => Promise<IncidentCommandCenterResponse>;
}
type LoadState = "loading" | "ready" | "error";

export default function DashboardPage({ loadFindings = getFindings, loadFindingIncidents = getFindingIncidents, loadIncident = getIncidentCommandCenter }: DashboardPageProps) {
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
    const requestedFindingId = useMemo(() => new URLSearchParams(location.search).get("findingId"), [location.search]);
    const finding = useMemo(() => findings.find(({ id }) => id === requestedFindingId) ?? null, [findings, requestedFindingId]);

    useEffect(() => {
        let current = true;
        setFindingsState("loading"); setFindings([]);
        void loaders.current.loadFindings().then((result) => { if (current) { setFindings(result); setFindingsState("ready"); } }).catch(() => { if (current) setFindingsState("error"); });
        return () => { current = false; };
    }, [refreshToken]);
    useEffect(() => {
        let current = true;
        setIncidents([]); setCommandCenter(null); setCommandCenterState("ready");
        if (findingsState !== "ready" || !finding) { setIncidentState("ready"); return () => { current = false; }; }
        setIncidentState("loading");
        void loaders.current.loadFindingIncidents(finding.id).then((result) => { if (current) { setIncidents(result); setIncidentState("ready"); } }).catch(() => { if (current) setIncidentState("error"); });
        return () => { current = false; };
    }, [finding, findingsState, refreshToken]);
    const linkedIncident = incidents[0] ?? null;
    useEffect(() => {
        let current = true;
        setCommandCenter(null);
        if (incidentState !== "ready" || !linkedIncident) { setCommandCenterState("ready"); return () => { current = false; }; }
        setCommandCenterState("loading");
        void loaders.current.loadIncident(linkedIncident.incident_id).then((result) => {
            if (!current) return;
            if (result.incident.incident_id === linkedIncident.incident_id) { setCommandCenter(result); setCommandCenterState("ready"); } else setCommandCenterState("error");
        }).catch(() => { if (current) setCommandCenterState("error"); });
        return () => { current = false; };
    }, [incidentState, linkedIncident]);

    const openFindings = (findingId?: string, ti = false) => {
        workspaceContext?.setWorkspace(WorkspaceId.DECISION_CENTER);
        const query = findingId ? `?findingId=${encodeURIComponent(findingId)}${ti ? "&focus=threat-intelligence" : ""}` : "";
        navigate(`/findings${query}`);
    };
    const openIncident = () => { workspaceContext?.setWorkspace(WorkspaceId.INCIDENT_RESPONSE); navigate("/incident-response"); };
    const openCommandCenter = (id: string) => { workspaceContext?.setWorkspace(WorkspaceId.INCIDENT_RESPONSE); navigate(`/incident-response/incidents/${encodeURIComponent(id)}/command-center`); };
    const toolbar = <SOCWorkspaceToolbar onRefresh={() => setRefreshToken((value) => value + 1)} refreshing={[findingsState, incidentState, commandCenterState].includes("loading")} compact />;
    if (findingsState === "loading") return <DashboardMessage toolbar={toolbar} progress title="Loading SOC dashboard" detail="Retrieving canonical findings." />;
    if (findingsState === "error") return <DashboardMessage toolbar={toolbar} severity="error" title="SOC dashboard unavailable" detail="Live findings could not be loaded." />;
    if (!finding) {
        const detail = requestedFindingId ? "The requested findingId does not match a loaded canonical finding." : findings.length === 0 ? "No live findings available." : "Select a finding to open an investigation dashboard.";
        return <DashboardMessage toolbar={toolbar} title="No active investigation" detail={detail} action={<Button variant="contained" onClick={() => openFindings()}>Open Findings</Button>} />;
    }

    const incidentStatus = incidentState === "loading" ? "Loading" : incidentState === "error" ? "Unavailable" : linkedIncident?.lifecycle_status ?? "Not available";
    const commandCenterStatus = commandCenterState === "loading" ? "Loading" : commandCenterState === "error" ? "Unavailable" : commandCenter ? "Loaded" : "Not available";
    const evidencePanel = <><Typography variant="overline" color="primary.main">EVIDENCE</Typography><Typography variant="h6">Persisted references</Typography><References references={commandCenter?.evidence ?? []} unavailable="No persisted evidence references are available." /></>;
    const incidentContext = <Stack spacing={1}>
        {incidentState === "error" && <Alert severity="error">Finding-to-Incident context could not be loaded.</Alert>}
        {commandCenterState === "error" && <Alert severity="error">Incident Command Center context could not be loaded.</Alert>}
        {linkedIncident && <Typography variant="body2">{linkedIncident.relationship_role} · {linkedIncident.lifecycle_status}</Typography>}
        {linkedIncident && (commandCenter ? <><Typography variant="body2" sx={{ fontWeight: 700 }}>{commandCenter.incident.title}</Typography>{commandCenter.incident.description && <Typography variant="body2">{commandCenter.incident.description}</Typography>}<Typography variant="caption" color="text.secondary">Created {commandCenter.incident.created_at} · Updated {commandCenter.incident.updated_at}</Typography></> : <Typography variant="body2" color="text.secondary">Canonical incident details are not available in this dashboard.</Typography>)}
        <Box component="section" aria-label="Chronological timeline"><Typography variant="subtitle2">Chronological timeline</Typography>{commandCenter?.activities.length ? <Stack component="ol" spacing={0.5} sx={{ pl: 2.5 }}>{commandCenter.activities.map((activity) => <Box component="li" key={activity.activity_id}><Typography variant="body2">{activity.occurred_at} — {activity.description}</Typography><Typography variant="caption" color="text.secondary">{activity.activity_type} · {activity.activity_id}</Typography></Box>)}</Stack> : <Typography variant="body2" color="text.secondary">No canonical incident activities are available.</Typography>}</Box>
    </Stack>;
    const relevantFindings = <Stack spacing={0.25}><Typography variant="body2" sx={{ fontWeight: 700 }}>{finding.title}</Typography><Typography variant="caption" color="text.secondary">{finding.id} · {finding.source}</Typography></Stack>;
    const assetContext = <Stack spacing={0.25}><Typography variant="body2">{finding.asset}</Typography><Typography variant="caption" color="text.secondary">Threat Intelligence relationship unavailable</Typography></Stack>;
    return <SOCAnalystCockpit finding={finding} incident={linkedIncident} commandCenterStatus={commandCenterStatus} evidenceAvailable={Boolean(commandCenter?.evidence.length)} incidentContextValue={linkedIncident?.incident_id ?? "Not available"} incidentContextStatus={incidentStatus} findingsError={false} incidentContextError={incidentState === "error" || commandCenterState === "error"} toolbar={toolbar} evidencePanel={evidencePanel} relevantFindings={relevantFindings} incidentContext={incidentContext} assetContext={assetContext} onFinding={openFindings} onThreatIntelligence={(id) => openFindings(id, true)} onIncident={openIncident} onOpenFinding={openFindings} onOpenThreatIntelligence={(id) => openFindings(id, true)} onCommandCenter={openCommandCenter} />;
}

function DashboardMessage({ toolbar, title, detail, action, progress = false, severity = "info" }: { toolbar: ReactNode; title: string; detail: string; action?: ReactNode; progress?: boolean; severity?: "info" | "error" }) {
    return <Stack component="main" aria-label="Analyst workspace" spacing={1.25}>{toolbar}<Alert severity={severity} icon={progress ? <CircularProgress size={20} /> : undefined}><Typography sx={{ fontWeight: 700 }}>{title}</Typography><Typography variant="body2">{detail}</Typography>{action && <Box sx={{ mt: 1 }}>{action}</Box>}</Alert></Stack>;
}
function References({ references, unavailable }: { references: readonly IncidentReference[]; unavailable: string }) {
    if (!references.length) return <Typography color="text.secondary">{unavailable}</Typography>;
    return <Stack component="ul" sx={{ pl: 2 }}>{references.map((reference) => <Typography component="li" variant="body2" key={reference.reference_id}>{reference.reference_id}{reference.source ? ` · ${reference.source}` : ""}</Typography>)}</Stack>;
}
