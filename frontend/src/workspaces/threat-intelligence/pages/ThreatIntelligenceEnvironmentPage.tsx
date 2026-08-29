import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Panel from "@/ui/panel/Panel";
import type { FindingSummary } from "@/workspaces/soc/findings/FindingSummary";
import { getFindings } from "@/workspaces/soc/findings/FindingsApiClient";
import ThreatIntelligencePageHeader from "./ThreatIntelligencePageHeader";

interface ThreatIntelligenceEnvironmentPageProps { loadFindings?: () => Promise<readonly FindingSummary[]>; }
export interface EnvironmentFindingsProps { findings: readonly FindingSummary[]; loading: boolean; error: boolean; compact?: boolean; }

export function EnvironmentFindings({ findings, loading, error, compact = false }: EnvironmentFindingsProps) {
    const navigate = useNavigate();
    const [query, setQuery] = useState("");
    const normalizedQuery = query.trim().toLocaleLowerCase();
    const filteredFindings = normalizedQuery === "" ? findings : findings.filter((finding) => [finding.id, finding.title, finding.asset, finding.source, finding.vendorSeverity].some((field) => field.toLocaleLowerCase().includes(normalizedQuery)));

    if (loading) return <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}><CircularProgress size={20} /><Typography>Loading internal findings…</Typography></Stack>;
    if (error) return <Alert severity="error">Internal findings are currently unavailable.</Alert>;
    if (findings.length === 0) return <Alert severity="info">No internal findings are available.</Alert>;

    return <Stack spacing={compact ? 1.5 : 3} className={compact ? "ti-environment-compact" : undefined}>
        <TextField label="Search findings" placeholder="Finding ID, title, asset, source or vendor severity" value={query} onChange={(event) => setQuery(event.target.value)} fullWidth size={compact ? "small" : "medium"} slotProps={{ htmlInput: { "aria-label": "Search findings" } }} />
        {filteredFindings.length === 0 && <Alert severity="info">No findings match the current search.</Alert>}
        <div className={compact ? "ti-environment-results" : undefined}>
            {filteredFindings.map((finding) => <Panel key={finding.id} component="article" className={compact ? "ti-finding-row" : undefined}>
                <Stack spacing={1.5}>
                    <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ justifyContent: "space-between", alignItems: { md: "center" } }}>
                        <Typography variant={compact ? "body2" : "h6"}>{finding.title}</Typography>
                        {!compact && <Chip label="TI relevance: Not evaluated" size="small" variant="outlined" />}
                    </Stack>
                    {compact ? <div className="ti-finding-fields"><span>{finding.id}</span><span>{finding.asset}</span><span>{finding.source}</span><span>{finding.vendorSeverity}</span></div> : <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                        <Chip label={`Source ${finding.source}`} size="small" /><Chip label={`Asset ${finding.asset}`} size="small" /><Chip label={`Vendor severity ${finding.vendorSeverity}`} size="small" /><Chip label="TI evidence: Not evaluated" size="small" variant="outlined" /><Chip label="Completeness: Not evaluated" size="small" variant="outlined" />
                    </Stack>}
                    <Button variant="outlined" size="small" onClick={() => navigate(`/findings?findingId=${encodeURIComponent(finding.id)}&focus=threat-intelligence`)}>Open finding-scoped Threat Intelligence</Button>
                </Stack>
            </Panel>)}
        </div>
    </Stack>;
}

export default function ThreatIntelligenceEnvironmentPage({ loadFindings = getFindings }: ThreatIntelligenceEnvironmentPageProps) {
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);
    useEffect(() => { let active = true; loadFindings().then((result) => { if (active) setFindings(result); }).catch(() => { if (active) setError(true); }).finally(() => { if (active) setLoading(false); }); return () => { active = false; }; }, [loadFindings]);
    return <Stack spacing={3}><ThreatIntelligencePageHeader eyebrow="Internal environment context" title="Our Environment" description="Internal findings are shown from the existing live source. Threat-intelligence matching and environment relevance remain not evaluated until the backend supplies those statements." /><EnvironmentFindings findings={findings} loading={loading} error={error} /></Stack>;
}
