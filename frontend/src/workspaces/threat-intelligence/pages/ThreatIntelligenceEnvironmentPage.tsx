import { useEffect, useState } from "react";

import Alert from "@mui/material/Alert";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import { useNavigate } from "react-router-dom";

import Panel from "@/ui/panel/Panel";
import type { FindingSummary } from "@/workspaces/soc/findings/FindingSummary";
import { getFindings } from "@/workspaces/soc/findings/FindingsApiClient";

import ThreatIntelligencePageHeader from "./ThreatIntelligencePageHeader";

interface ThreatIntelligenceEnvironmentPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
}

export default function ThreatIntelligenceEnvironmentPage({
    loadFindings = getFindings,
}: ThreatIntelligenceEnvironmentPageProps) {
    const navigate = useNavigate();
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    const [query, setQuery] = useState("");

    useEffect(() => {
        let active = true;

        loadFindings()
            .then((result) => {
                if (active) setFindings(result);
            })
            .catch(() => {
                if (active) setError(true);
            })
            .finally(() => {
                if (active) setLoading(false);
            });

        return () => {
            active = false;
        };
    }, [loadFindings]);

    const normalizedQuery = query.trim().toLocaleLowerCase();
    const filteredFindings = normalizedQuery === ""
        ? findings
        : findings.filter((finding) => [
            finding.id,
            finding.title,
            finding.asset,
            finding.source,
            finding.vendorSeverity,
        ].some((field) => field.toLocaleLowerCase().includes(normalizedQuery)));

    return (
        <Stack spacing={3}>
            <ThreatIntelligencePageHeader
                eyebrow="Internal environment context"
                title="Our Environment"
                description="Internal findings are shown from the existing live source. Threat-intelligence matching and environment relevance remain not evaluated until the backend supplies those statements."
            />

            {loading && (
                <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                    <CircularProgress size={20} />
                    <Typography>Loading internal findings…</Typography>
                </Stack>
            )}

            {error && (
                <Alert severity="error">
                    Internal findings are currently unavailable.
                </Alert>
            )}

            {!loading && !error && findings.length > 0 && (
                <TextField
                    label="Search findings"
                    placeholder="Title, asset, source or finding ID"
                    value={query}
                    onChange={(event) => setQuery(event.target.value)}
                    fullWidth
                    slotProps={{ htmlInput: { "aria-label": "Search findings" } }}
                />
            )}

            {!loading && !error && findings.length === 0 && (
                <Alert severity="info">No internal findings are available.</Alert>
            )}

            {!loading && !error && findings.length > 0 && filteredFindings.length === 0 && (
                <Alert severity="info">No findings match the current search.</Alert>
            )}

            {!loading && !error && filteredFindings.map((finding) => (
                <Panel key={finding.id} component="article">
                    <Stack spacing={1.5}>
                        <Stack
                            direction={{ xs: "column", md: "row" }}
                            spacing={1}
                            sx={{ justifyContent: "space-between", alignItems: { md: "center" } }}
                        >
                            <Typography variant="h6">{finding.title}</Typography>
                            <Chip label="TI relevance: Not evaluated" size="small" variant="outlined" />
                        </Stack>
                        <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                            <Chip label={`Source ${finding.source}`} size="small" />
                            <Chip label={`Asset ${finding.asset}`} size="small" />
                            <Chip label={`Vendor severity ${finding.vendorSeverity}`} size="small" />
                            <Chip label="TI evidence: Not evaluated" size="small" variant="outlined" />
                            <Chip label="Completeness: Not evaluated" size="small" variant="outlined" />
                        </Stack>
                        <Button
                            variant="outlined"
                            size="small"
                            onClick={() => navigate(`/findings?findingId=${encodeURIComponent(finding.id)}&focus=threat-intelligence`)}
                        >
                            Open finding-scoped Threat Intelligence
                        </Button>
                    </Stack>
                </Panel>
            ))}
        </Stack>
    );
}
