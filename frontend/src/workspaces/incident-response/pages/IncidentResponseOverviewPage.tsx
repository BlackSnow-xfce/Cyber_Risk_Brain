import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { Link } from "react-router-dom";

import type { IncidentQueueItem } from "../IncidentQueue";
import { getIncidents } from "../IncidentQueueApiClient";
import "./IncidentResponseOverviewPage.css";

type IncidentLoader = () => Promise<IncidentQueueItem[]>;
interface Props { loadIncidents?: IncidentLoader; }
const activeStatuses = new Set(["open", "investigating"]);
const unavailable = [
    ["Critical Incidents", "Unavailable"],
    ["MTTR", "Unavailable"],
    ["Contained Incidents", "Unavailable"],
    ["Open Tasks", "Not connected"],
] as const;

export default function IncidentResponseOverviewPage({ loadIncidents = getIncidents }: Props) {
    const [incidents, setIncidents] = useState<IncidentQueueItem[]>([]);
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        let current = true;
        setLoading(true);
        setError(false);
        void loadIncidents().then((items) => { if (current) setIncidents(items); })
            .catch(() => { if (current) setError(true); })
            .finally(() => { if (current) setLoading(false); });
        return () => { current = false; };
    }, [loadIncidents]);

    const active = useMemo(() => incidents.filter(({ lifecycle_status }) => activeStatuses.has(lifecycle_status)), [incidents]);
    const normalizedQuery = query.trim().toLowerCase();
    const visible = useMemo(() => active.filter((incident) => !normalizedQuery || [
        incident.incident_id, incident.title, incident.lifecycle_status,
        incident.created_at, incident.updated_at,
    ].some((value) => value.toLowerCase().includes(normalizedQuery))), [active, normalizedQuery]);

    return <main className="incident-overview">
        <header className="incident-overview__header"><Typography component="h1">Incident Response</Typography><Typography component="p">Overview</Typography></header>
        <section className="incident-panel incident-snapshot" aria-labelledby="snapshot-title">
            <Typography component="h2" id="snapshot-title">Incident Response Snapshot</Typography>
            <div className="incident-snapshot__grid">
                <article className="snapshot-instrument"><Typography component="h3">Active Incidents</Typography><div className="snapshot-instrument__value" aria-live="polite">{loading ? <CircularProgress size={22} aria-label="Loading active incidents" /> : error ? "Unavailable" : active.length}</div><Typography component="p">Open and investigating</Typography></article>
                {unavailable.map(([label, state]) => <article className="snapshot-instrument" key={label}><Typography component="h3">{label}</Typography><div className="snapshot-instrument__value snapshot-instrument__value--state">{state}</div><Typography component="p">No authoritative source</Typography></article>)}
            </div>
        </section>
        <div className="incident-overview__grid incident-overview__grid--middle">
            <section className="incident-panel active-incidents" aria-labelledby="active-title">
                <div className="active-incidents__toolbar"><Typography component="h2" id="active-title">Active Incidents</Typography><Button component={Link} to="/incident-response/queue" variant="outlined" size="small">Open queue</Button></div>
                <TextField className="active-incidents__search" size="small" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search active incidents" slotProps={{ htmlInput: { "aria-label": "Search active incidents" } }} />
                <div className="active-incidents__stage">
                    {loading && <State><CircularProgress size={22} />Loading incidents...</State>}
                    {!loading && error && <State alert>Incident queue could not be loaded.</State>}
                    {!loading && !error && incidents.length === 0 && <State>No persisted incidents are available.</State>}
                    {!loading && !error && incidents.length > 0 && active.length === 0 && <State>No active incidents are available.</State>}
                    {!loading && !error && active.length > 0 && visible.length === 0 && <State>No active incidents match the search.</State>}
                    {!loading && !error && visible.length > 0 && <div className="incident-table" role="table" aria-label="Active incidents">
                        <div className="incident-table__header" role="row"><span role="columnheader">Incident</span><span role="columnheader">Status</span><span role="columnheader">Created / Updated</span></div>
                        {visible.map((incident) => <Link className="incident-table__row" key={incident.incident_id} to={`/incident-response/incidents/${encodeURIComponent(incident.incident_id)}/command-center`}><span><strong>{incident.title}</strong><small>{incident.incident_id}</small></span><span>{incident.lifecycle_status}</span><span><small>{incident.created_at}</small><small>{incident.updated_at}</small></span></Link>)}
                    </div>}
                </div>
            </section>
            <UnavailablePanel title="Response Status" state="Unavailable" visual />
        </div>
        <div className="incident-overview__grid incident-overview__grid--lower"><UnavailablePanel title="Response Playbooks" state="Not connected" /><UnavailablePanel title="Recent Activity" state="Unavailable" /></div>
    </main>;
}

function State({ children, alert = false }: { children: ReactNode; alert?: boolean }) {
    return <div className="incident-state" role={alert ? "alert" : undefined}>{children}</div>;
}

function UnavailablePanel({ title, state, visual = false }: { title: string; state: string; visual?: boolean }) {
    const id = `${title.toLowerCase().replaceAll(" ", "-")}-title`;
    return <section className="incident-panel unavailable-panel" aria-labelledby={id}><Typography component="h2" id={id}>{title}</Typography><div className={`unavailable-panel__stage${visual ? " unavailable-panel__stage--status" : ""}`}>{visual && <div className="response-status-visual" aria-hidden="true"><span /><span /><span /></div>}<Typography component="p" className="unavailable-panel__state">{state}</Typography><Typography component="p">No authoritative overview data source</Typography></div></section>;
}
