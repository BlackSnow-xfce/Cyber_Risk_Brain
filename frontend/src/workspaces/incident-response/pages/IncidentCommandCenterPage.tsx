import { useEffect, useMemo, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useLocation } from "react-router-dom";

import Panel from "@/ui/panel/Panel";

import type {
    AnalystNote,
    IncidentActivity,
    IncidentCommandCenterResponse,
    IncidentPrincipal,
    IncidentReference,
    IncidentProjectionSection,
} from "../IncidentCommandCenter";
import {
    getIncidentCommandCenter,
    IncidentCommandCenterRequestError,
} from "../IncidentCommandCenterApiClient";

interface IncidentCommandCenterPageProps {
    incidentId?: string;
    loadIncident?: (incidentId: string) => Promise<IncidentCommandCenterResponse>;
}

export default function IncidentCommandCenterPage({
    incidentId: providedIncidentId,
    loadIncident = getIncidentCommandCenter,
}: IncidentCommandCenterPageProps) {
    const location = useLocation();
    const routeIncidentId = useMemo(
        () => extractIncidentId(location.pathname),
        [location.pathname],
    );
    const incidentId = providedIncidentId ?? routeIncidentId;
    const [result, setResult] = useState<IncidentCommandCenterResponse | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (!incidentId?.trim()) {
            setResult(null);
            setError(null);
            setLoading(false);
            return;
        }

        let current = true;
        setLoading(true);
        setError(null);
        setResult(null);
        void loadIncident(incidentId)
            .then((payload) => {
                if (current) setResult(payload);
            })
            .catch((requestError: unknown) => {
                if (current) setError(errorMessage(requestError));
            })
            .finally(() => {
                if (current) setLoading(false);
            });

        return () => {
            current = false;
        };
    }, [incidentId, loadIncident]);

    if (!incidentId?.trim()) {
        return (
            <Stack spacing={3}>
                <PageHeader />
                <Alert severity="info">
                    Open this view with an incident ID, for example
                    `/incident-response/incidents/&lt;incident-id&gt;/command-center`.
                </Alert>
            </Stack>
        );
    }

    return (
        <Stack spacing={3}>
            <PageHeader />
            {loading && (
                <Panel component="section">
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                        <CircularProgress size={22} />
                        <Typography>Loading incident command center…</Typography>
                    </Stack>
                </Panel>
            )}
            {error && <Alert severity="error">{error}</Alert>}
            {result && <CommandCenterContent result={result} />}
        </Stack>
    );
}

function PageHeader() {
    return (
        <Box component="header">
            <Typography variant="overline" color="error.main">
                Incident Response
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
                Incident Command Center
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 780 }}>
                Read-only projection of the canonical incident context and its
                owner-boundary references.
            </Typography>
        </Box>
    );
}

function CommandCenterContent({ result }: { result: IncidentCommandCenterResponse }) {
    const incident = result.incident;
    return (
        <Stack spacing={2}>
            <Panel component="section">
                <Stack spacing={1.5}>
                    <Stack direction="row" spacing={1} sx={{ alignItems: "center", flexWrap: "wrap" }}>
                        <Typography variant="h5">{incident.title}</Typography>
                        <Chip label={incident.lifecycle_status} size="small" color="primary" />
                    </Stack>
                    <Detail label="Incident ID" value={incident.incident_id} />
                    <Detail label="Source" value={incident.source} />
                    <Detail label="Source Reference" value={incident.source_reference} />
                    <Detail label="Contract Version" value={result.contract_version} />
                    <Detail label="Created" value={formatDate(incident.created_at)} />
                    <Detail label="Updated" value={formatDate(incident.updated_at)} />
                    {incident.description && <Typography color="text.secondary">{incident.description}</Typography>}
                </Stack>
            </Panel>

            <Panel component="section">
                <Typography variant="h6">Ownership & Participants</Typography>
                <Typography sx={{ mt: 1 }}>
                    Owner: {incident.owner ? principalLabel(incident.owner) : "Not available"}
                </Typography>
                <Collection
                    label="Participants"
                    values={incident.participants.map((item) => `${principalLabel(item.principal)} (${item.role})`)}
                />
            </Panel>

            <Box component="section" sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(2, minmax(0, 1fr))" }, gap: 2 }}>
                <ReferenceSection title="Findings" references={result.findings} empty="No findings referenced." />
                <ReferenceSection title="Canonical Assets" references={result.assets} empty="No assets referenced." />
                <ReferenceSection title="Threat Intelligence" references={result.threat_intelligence} empty="No threat intelligence referenced." />
                <ReferenceSection title="Evidence" references={result.evidence} empty="No evidence referenced." />
                <ReferenceSection title="Decisions" references={result.decisions} empty="No decisions referenced." />
            </Box>

            <Panel component="section">
                <Typography variant="h6">Completeness & Missing Context</Typography>
                <Detail label="Status" value={result.completeness.status} />
                <Detail label="Source" value={result.completeness.source_reference} />
                <Collection label="Missing Context" values={result.missing_context} empty="No missing context reported." />
                <Stack spacing={1.5} sx={{ mt: 2 }}>
                    {result.sections.map((section) => <ProjectionSection key={section.section} section={section} />)}
                </Stack>
            </Panel>

            <Panel component="section">
                <Typography variant="h6">Analyst Notes</Typography>
                {result.notes.length === 0 ? <Typography color="text.secondary" sx={{ mt: 1 }}>No analyst notes available.</Typography> : result.notes.map((note) => <Note key={note.note_version_id} note={note} />)}
            </Panel>

            <Panel component="section">
                <Typography variant="h6">Incident Activity</Typography>
                {result.activities.length === 0 ? <Typography color="text.secondary" sx={{ mt: 1 }}>No incident activity available.</Typography> : result.activities.map((activity) => <Activity key={activity.activity_id} activity={activity} />)}
            </Panel>
        </Stack>
    );
}

function ReferenceSection({ title, references, empty }: { title: string; references: IncidentReference[]; empty: string }) {
    return (
        <Panel component="section">
            <Typography variant="h6">{title}</Typography>
            <Collection label="References" values={references.map((reference) => reference.reference_id)} empty={empty} />
        </Panel>
    );
}

function ProjectionSection({ section }: { section: IncidentProjectionSection }) {
    return (
        <Box>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                <Typography sx={{ fontWeight: 600 }}>{section.section}</Typography>
                <Chip label={section.status} size="small" variant="outlined" />
            </Stack>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                References: {section.reference_ids.length || "none"}
            </Typography>
            {section.missing_context.length > 0 && <Typography variant="body2" color="warning.main">Missing: {section.missing_context.join(", ")}</Typography>}
        </Box>
    );
}

function Collection({ label, values, empty }: { label: string; values: string[]; empty?: string }) {
    return (
        <Box sx={{ mt: 1 }}>
            <Typography variant="body2" color="text.secondary">{label}</Typography>
            {values.length === 0 ? <Typography color="text.secondary">{empty ?? "No entries available."}</Typography> : values.map((value) => <Typography key={value} variant="body2">{value}</Typography>)}
        </Box>
    );
}

function Detail({ label, value }: { label: string; value: string }) {
    return <Typography variant="body2"><strong>{label}:</strong> {value}</Typography>;
}

function Note({ note }: { note: AnalystNote }) {
    return <Box sx={{ mt: 1.5 }}><Typography variant="body2">{note.content}</Typography><Typography variant="caption" color="text.secondary">{principalLabel(note.author)} · {formatDate(note.created_at)} · v{note.version}</Typography><Divider sx={{ mt: 1.5 }} /></Box>;
}

function Activity({ activity }: { activity: IncidentActivity }) {
    return <Box sx={{ mt: 1.5 }}><Typography variant="body2">{activity.description}</Typography><Typography variant="caption" color="text.secondary">{activity.activity_type} · {principalLabel(activity.actor)} · {formatDate(activity.occurred_at)}</Typography><Divider sx={{ mt: 1.5 }} /></Box>;
}

function principalLabel(principal: IncidentPrincipal): string {
    return `${principal.principal_type}:${principal.principal_id}`;
}

function formatDate(value: string): string {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function extractIncidentId(pathname: string): string | null {
    const match = pathname.match(/^\/incident-response\/incidents\/([^/]+)\/command-center\/?$/);
    return match ? decodeURIComponent(match[1]) : null;
}

function errorMessage(error: unknown): string {
    if (!(error instanceof IncidentCommandCenterRequestError)) return "Incident command center could not be loaded.";
    if (error.status === null) return "The PredatorAI backend is not reachable.";
    if (error.status === 404) return "Incident was not found.";
    if (error.status === 503) return "The incident source is currently unavailable.";
    if (error.status === 500) return "The incident command-center data is invalid or unavailable.";
    return "Incident command center could not be loaded.";
}
