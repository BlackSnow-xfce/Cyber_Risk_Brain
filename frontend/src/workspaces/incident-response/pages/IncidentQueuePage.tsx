import { useEffect, useMemo, useState } from "react";
import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { Link } from "react-router-dom";

import Panel from "@/ui/panel/Panel";

import type { IncidentQueueItem } from "../IncidentQueue";
import {
    getIncidents,
    IncidentQueueRequestError,
} from "../IncidentQueueApiClient";

export default function IncidentQueuePage() {
    const [incidents, setIncidents] = useState<IncidentQueueItem[]>([]);
    const [query, setQuery] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let current = true;
        setLoading(true);
        setError(null);
        void getIncidents()
            .then((items) => {
                if (current) setIncidents(items);
            })
            .catch((requestError: unknown) => {
                if (!current) return;
                setError(
                    requestError instanceof IncidentQueueRequestError && requestError.status === 503
                        ? "Incident data source is not connected."
                        : "Incident queue could not be loaded.",
                );
            })
            .finally(() => {
                if (current) setLoading(false);
            });
        return () => {
            current = false;
        };
    }, []);

    const normalizedQuery = query.trim().toLowerCase();
    const filteredIncidents = useMemo(
        () => incidents.filter((incident) => {
            if (!normalizedQuery) return true;
            return [
                incident.incident_id,
                incident.title,
                incident.lifecycle_status,
                incident.owner?.principal_id ?? "",
                incident.source,
            ].some((value) => value.toLowerCase().includes(normalizedQuery));
        }),
        [incidents, normalizedQuery],
    );

    return (
        <Stack spacing={2.5}>
            <Box component="header">
                <Typography variant="overline" color="error.main">Incident Response</Typography>
                <Typography variant="h4" sx={{ fontWeight: 700 }}>Incident Queue</Typography>
                <Typography color="text.secondary" sx={{ mt: 0.5 }}>
                    Review persisted Incident Contexts and open a technical investigation.
                </Typography>
            </Box>

            <Panel component="section">
                <TextField
                    fullWidth
                    size="small"
                    label="Search incidents"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    placeholder="ID, title, lifecycle, owner or source"
                    slotProps={{ htmlInput: { "aria-label": "Search incidents" } }}
                />
            </Panel>

            {loading && <Panel><Stack direction="row" spacing={1} sx={{ alignItems: "center" }}><CircularProgress size={18} /><Typography>Loading incidents…</Typography></Stack></Panel>}
            {error && <Alert severity="error">{error}</Alert>}
            {!loading && !error && incidents.length === 0 && (
                <Alert severity="info">No persisted incidents are available.</Alert>
            )}
            {!loading && !error && incidents.length > 0 && filteredIncidents.length === 0 && (
                <Alert severity="info">No incidents match “{query}”.</Alert>
            )}
            {!loading && !error && filteredIncidents.length > 0 && (
                <Stack spacing={1.25} component="section" aria-label="Incident queue">
                    {filteredIncidents.map((incident) => (
                        <Panel key={incident.incident_id} component="article" sx={{ p: 1.5 }}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ alignItems: { md: "center" }, justifyContent: "space-between" }}>
                                <Box sx={{ minWidth: 0 }}>
                                    <Typography variant="h6" sx={{ fontSize: "1rem" }}>{incident.title}</Typography>
                                    <Typography variant="body2" color="text.secondary">{incident.incident_id}</Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        {incident.lifecycle_status} · {incident.source} · {incident.owner?.principal_id ?? "No owner"}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                                        Created {formatTimestamp(incident.created_at)} · Updated {formatTimestamp(incident.updated_at)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>
                                        Participants {incident.participant_count} · Findings {incident.finding_count} · Assets {incident.asset_count} · TI {incident.threat_intelligence_count} · Evidence {incident.evidence_count}
                                    </Typography>
                                </Box>
                                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                                    <Button
                                        component={Link}
                                        to={`/incident-response/incidents/${encodeURIComponent(incident.incident_id)}/command-center`}
                                        size="small"
                                        variant="outlined"
                                    >
                                        Open Command Center
                                    </Button>
                                </Stack>
                            </Stack>
                        </Panel>
                    ))}
                </Stack>
            )}
        </Stack>
    );
}

function formatTimestamp(value: string): string {
    const timestamp = new Date(value);
    return Number.isNaN(timestamp.getTime()) ? value : timestamp.toLocaleString();
}
