import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import {
    businessService,
    evidenceStatus,
    missingEvidence,
    riskScore,
    technicalBand,
    type RiskManagerRecord,
} from "../RiskManagerProjection";
import { useRiskManagerProjection } from "../useRiskManagerProjection";

function bandColor(band: string): "error" | "warning" | "info" | "default" {
    if (band === "CRITICAL") return "error";
    if (band === "HIGH") return "warning";
    if (band === "MEDIUM") return "info";
    return "default";
}

function MetricCard({ label, value, detail }: { label: string; value: string | number; detail: string }) {
    return (
        <Panel component="section" sx={{ minHeight: 132 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: "0.08em" }}>
                {label}
            </Typography>
            <Typography variant="h3" sx={{ mt: 0.75, fontWeight: 750 }}>
                {value}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
                {detail}
            </Typography>
        </Panel>
    );
}

function RiskQueueRow({ record }: { record: RiskManagerRecord }) {
    const band = technicalBand(record);
    const missing = missingEvidence(record);
    return (
        <Box
            component="article"
            sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", lg: "minmax(260px,2fr) 110px 90px minmax(170px,1fr) 130px minmax(180px,1fr)" },
                gap: 1.5,
                alignItems: "center",
                py: 1.5,
                borderBottom: "1px solid",
                borderColor: "divider",
            }}
        >
            <Box sx={{ minWidth: 0 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }} noWrap>
                    {record.finding.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    {record.finding.asset} · {record.finding.source}
                </Typography>
            </Box>
            <Chip label={band} size="small" variant="outlined" color={bandColor(band)} sx={{ justifySelf: "start" }} />
            <Typography variant="body2" sx={{ fontWeight: 700 }}>{riskScore(record)}</Typography>
            <Typography variant="body2">{businessService(record)}</Typography>
            <Chip
                label={evidenceStatus(record)}
                size="small"
                variant="outlined"
                color={evidenceStatus(record) === "READY" ? "success" : "warning"}
                sx={{ justifySelf: "start" }}
            />
            <Typography variant="caption" color={missing.length ? "warning.main" : "text.secondary"}>
                {missing.length ? `${missing.length} missing evidence requirement${missing.length === 1 ? "" : "s"}` : "Evidence complete"}
            </Typography>
        </Box>
    );
}

export default function RiskManagerOverviewPage() {
    const { projection, loading, error, reload } = useRiskManagerProjection();

    return (
        <Stack spacing={3}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { md: "flex-end" } }}>
                <Box component="header">
                    <Typography variant="overline" color="info.main">
                        Enterprise risk governance
                    </Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        Risk Manager Mission Console
                    </Typography>
                    <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 820 }}>
                        Live risk context from the existing finding, asset, threat-intelligence and business-context pipeline. Governance claims without an authoritative source remain explicitly unavailable.
                    </Typography>
                </Box>
                <Button variant="outlined" onClick={reload} disabled={loading}>
                    Refresh risk context
                </Button>
            </Stack>

            {loading && !projection && (
                <Panel component="section">
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                        <CircularProgress size={20} />
                        <Typography>Loading authoritative finding risk context…</Typography>
                    </Stack>
                </Panel>
            )}

            {error && <Alert severity="error">{error}</Alert>}

            {projection && (
                <>
                    {projection.unresolvedContexts > 0 && (
                        <Alert severity="warning">
                            Risk context is unavailable for {projection.unresolvedContexts} finding{projection.unresolvedContexts === 1 ? "" : "s"}. Those findings remain visible and are not silently scored.
                        </Alert>
                    )}

                    <Box
                        component="section"
                        aria-label="Risk Manager summary"
                        sx={{
                            display: "grid",
                            gridTemplateColumns: { xs: "1fr", sm: "repeat(2,1fr)", xl: "repeat(4,1fr)" },
                            gap: 2,
                        }}
                    >
                        <MetricCard label="Findings in scope" value={projection.totalFindings} detail="Canonical scanner findings" />
                        <MetricCard label="Assessed" value={projection.assessedFindings} detail="Evidence-gated risk assessment available" />
                        <MetricCard label="Critical / High" value={projection.criticalFindings + projection.highFindings} detail={`${projection.criticalFindings} critical · ${projection.highFindings} high`} />
                        <MetricCard label="Business services" value={projection.businessServices.length} detail="Authoritatively resolved service relationships" />
                    </Box>

                    <Panel component="section">
                        <Stack spacing={2}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ justifyContent: "space-between", alignItems: { md: "center" } }}>
                                <Box>
                                    <Typography variant="h6">Prioritized risk queue</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        Ordered by the existing technical priority band. No new governance priority is calculated in the client.
                                    </Typography>
                                </Box>
                                <Chip label={`${projection.records.length} findings`} size="small" variant="outlined" />
                            </Stack>
                            <Divider />
                            <Box sx={{ display: { xs: "none", lg: "grid" }, gridTemplateColumns: "minmax(260px,2fr) 110px 90px minmax(170px,1fr) 130px minmax(180px,1fr)", gap: 1.5 }}>
                                {['Finding','Risk band','Score','Business service','Evidence','Governance gap'].map((label) => (
                                    <Typography key={label} variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: "0.06em" }}>{label}</Typography>
                                ))}
                            </Box>
                            <Box>
                                {projection.records.slice(0, 12).map((record) => <RiskQueueRow key={record.finding.id} record={record} />)}
                            </Box>
                        </Stack>
                    </Panel>

                    <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "1.35fr 1fr" }, gap: 2 }}>
                        <Panel component="section">
                            <Typography variant="h6">Business service exposure</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 2 }}>
                                Services are shown only when the existing business-context source resolves them.
                            </Typography>
                            <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                                {projection.businessServices.length ? projection.businessServices.map((service) => (
                                    <Chip key={service} label={service} variant="outlined" color="info" />
                                )) : <Typography variant="body2" color="text.secondary">No authoritative business service relationship is available.</Typography>}
                            </Stack>
                        </Panel>

                        <Panel component="section">
                            <Typography variant="h6">Governance readiness</Typography>
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 2 }}>
                                The current assessment pipeline does not yet provide authoritative workflow claims.
                            </Typography>
                            <Stack spacing={1.25}>
                                {['Accountable owner','Treatment state','Risk acceptance','SLA / deadline','Escalation state'].map((label) => (
                                    <Stack key={label} direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                                        <Typography variant="body2">{label}</Typography>
                                        <Chip label="NOT AVAILABLE" size="small" variant="outlined" color="warning" />
                                    </Stack>
                                ))}
                            </Stack>
                        </Panel>
                    </Box>
                </>
            )}
        </Stack>
    );
}
