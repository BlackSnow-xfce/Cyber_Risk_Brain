import { useState } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import RiskManagerCaseDetail from "../RiskManagerCaseDetail";
import {
    businessService,
    evidenceStatus,
    missingEvidence,
    riskScore,
    serviceCriticality,
    technicalBand,
    type RiskManagerRecord,
} from "../RiskManagerProjection";
import { useRiskManagerProjection } from "../useRiskManagerProjection";
import type { RiskManagerAreaId } from ".";

interface RiskManagerAreaPageProps {
    areaId: RiskManagerAreaId;
    title: string;
    description: string;
}

function bandColor(band: string): "error" | "warning" | "info" | "default" {
    if (band === "CRITICAL") return "error";
    if (band === "HIGH") return "warning";
    if (band === "MEDIUM") return "info";
    return "default";
}

function FindingRow({ record, selected, onSelect }: { record: RiskManagerRecord; selected: boolean; onSelect: () => void }) {
    const band = technicalBand(record);
    const missing = missingEvidence(record);
    return (
        <Box
            component="button"
            type="button"
            onClick={onSelect}
            aria-pressed={selected}
            sx={{
                display: "grid",
                gridTemplateColumns: { xs: "1fr", lg: "minmax(280px,2fr) 110px 80px minmax(170px,1fr) 130px" },
                gap: 1.5,
                width: "100%",
                py: 1.5,
                px: 1,
                border: 0,
                borderBottom: "1px solid",
                borderColor: "divider",
                borderRadius: 1,
                alignItems: "center",
                textAlign: "left",
                font: "inherit",
                color: "text.primary",
                backgroundColor: selected ? "action.selected" : "transparent",
                cursor: "pointer",
                "&:hover": { backgroundColor: "action.hover" },
            }}
        >
            <Box sx={{ minWidth: 0 }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700 }}>{record.finding.title}</Typography>
                <Typography variant="caption" color="text.secondary">{record.finding.asset} · {record.finding.source}</Typography>
            </Box>
            <Chip label={band} size="small" variant="outlined" color={bandColor(band)} sx={{ justifySelf: "start" }} />
            <Typography variant="body2" sx={{ fontWeight: 700 }}>{riskScore(record)}</Typography>
            <Typography variant="body2">{businessService(record)}</Typography>
            <Stack spacing={0.25}>
                <Typography variant="caption" color={evidenceStatus(record) === "READY" ? "success.main" : "warning.main"}>{evidenceStatus(record)}</Typography>
                {missing.length > 0 && <Typography variant="caption" color="text.secondary">{missing.length} missing</Typography>}
            </Stack>
        </Box>
    );
}

function FindingList({ records, selectedId, onSelect }: { records: readonly RiskManagerRecord[]; selectedId: string | null; onSelect: (id: string) => void }) {
    if (!records.length) return <Typography variant="body2" color="text.secondary">No matching findings are available.</Typography>;
    return <Box>{records.map((record) => <FindingRow key={record.finding.id} record={record} selected={record.finding.id === selectedId} onSelect={() => onSelect(record.finding.id)} />)}</Box>;
}

function ServiceView({ records }: { records: readonly RiskManagerRecord[] }) {
    const grouped = new Map<string, RiskManagerRecord[]>();
    for (const record of records) {
        const service = businessService(record);
        if (service === "NOT AVAILABLE") continue;
        grouped.set(service, [...(grouped.get(service) ?? []), record]);
    }
    if (!grouped.size) return <Typography variant="body2" color="text.secondary">No authoritative business-service relationships are available.</Typography>;
    return (
        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", lg: "repeat(2,1fr)" }, gap: 2 }}>
            {[...grouped.entries()].map(([service, serviceRecords]) => {
                const critical = serviceRecords.filter((record) => technicalBand(record) === "CRITICAL").length;
                const high = serviceRecords.filter((record) => technicalBand(record) === "HIGH").length;
                return (
                    <Panel key={service} component="article">
                        <Stack spacing={1.5}>
                            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                                <Typography variant="h6">{service}</Typography>
                                <Chip label={`${serviceRecords.length} findings`} size="small" variant="outlined" />
                            </Stack>
                            <Typography variant="body2" color="text.secondary">Service criticality: {serviceCriticality(serviceRecords[0])}</Typography>
                            <Stack direction="row" spacing={1}>
                                <Chip label={`${critical} critical`} size="small" color={critical ? "error" : "default"} variant="outlined" />
                                <Chip label={`${high} high`} size="small" color={high ? "warning" : "default"} variant="outlined" />
                            </Stack>
                        </Stack>
                    </Panel>
                );
            })}
        </Box>
    );
}

function BusinessImpactView({ records }: { records: readonly RiskManagerRecord[] }) {
    return (
        <Stack spacing={1.5}>
            {records.map((record) => {
                const readiness = record.context?.business_impact_classification_readiness;
                return (
                    <Panel key={record.finding.id} component="article">
                        <Stack spacing={1}>
                            <Stack direction={{ xs: "column", md: "row" }} spacing={1} sx={{ justifyContent: "space-between" }}>
                                <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>{record.finding.title}</Typography>
                                <Chip label={readiness?.status ?? "UNAVAILABLE"} size="small" variant="outlined" color={readiness?.status === "READY" ? "success" : "warning"} />
                            </Stack>
                            <Typography variant="body2" color="text.secondary">{businessService(record)} · {record.finding.asset}</Typography>
                            <Typography variant="body2">{readiness?.reason ?? "Business-impact classification readiness is not available."}</Typography>
                        </Stack>
                    </Panel>
                );
            })}
        </Stack>
    );
}

const workflowLabels: Partial<Record<RiskManagerAreaId, readonly string[]>> = {
    "treatment-plans": ["Treatment state", "Remediation blocker", "Compensating controls"],
    "risk-ownership": ["Accountable owner", "Assignment authority", "Assignment validity"],
    "risk-acceptance": ["Acceptance decision", "Authoritative approver", "Validity period"],
    exceptions: ["Exception decision", "Validity", "Revocation evidence"],
    compliance: ["Compliance mapping", "Control applicability", "Evidence"],
    policies: ["Risk policy", "SLA policy", "Policy version"],
    trends: ["Historical snapshots", "Projection timestamp", "Trend source"],
    "executive-reports": ["Decision projection", "Governance attention", "Executive evidence"],
};

export default function RiskManagerAreaPage({ areaId, title, description }: RiskManagerAreaPageProps) {
    const { projection, loading, error, reload } = useRiskManagerProjection();
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const records = projection?.records ?? [];
    const criticalRecords = records.filter((record) => ["CRITICAL", "HIGH"].includes(technicalBand(record)));
    const crownJewels = records.filter((record) => record.context?.asset_context.criticality?.toUpperCase() === "CRITICAL" || serviceCriticality(record) === "CRITICAL");
    const workflowFields = workflowLabels[areaId];
    const selectableRecords = areaId === "critical-risks" ? criticalRecords : areaId === "crown-jewels" ? crownJewels : records;
    const effectiveSelectedId = selectedId && selectableRecords.some((record) => record.finding.id === selectedId) ? selectedId : selectableRecords[0]?.finding.id ?? null;
    const selectedRecord = selectableRecords.find((record) => record.finding.id === effectiveSelectedId) ?? null;
    const showCaseWorkspace = areaId === "risk-register" || areaId === "critical-risks" || areaId === "crown-jewels";

    return (
        <Stack spacing={3}>
            <Stack direction={{ xs: "column", md: "row" }} spacing={2} sx={{ justifyContent: "space-between", alignItems: { md: "flex-end" } }}>
                <Box component="header">
                    <Typography variant="overline" color="info.main">Risk Manager</Typography>
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>{title}</Typography>
                    <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 760 }}>{description}</Typography>
                </Box>
                <Button variant="outlined" onClick={reload} disabled={loading}>Refresh</Button>
            </Stack>

            {loading && !projection && <Panel><Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}><CircularProgress size={20} /><Typography>Loading authoritative risk context…</Typography></Stack></Panel>}
            {error && <Alert severity="error">{error}</Alert>}

            {projection && (
                <>
                    {showCaseWorkspace && (
                        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", xl: "minmax(0,1.7fr) minmax(360px,0.9fr)" }, gap: 2, alignItems: "start" }}>
                            <Panel component="section">
                                <Typography variant="h6">{areaId === "risk-register" ? "Risk register" : areaId === "critical-risks" ? "Critical and high technical risk" : "Critical assets and services"}</Typography>
                                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5, mb: 1.5 }}>
                                    {areaId === "risk-register" ? "Canonical findings enriched with the existing evidence-gated risk and business context." : areaId === "critical-risks" ? "Uses the existing technical priority projection; no client-side governance priority is derived." : "Only authoritatively resolved criticality is shown."}
                                </Typography>
                                <Divider />
                                <FindingList records={selectableRecords} selectedId={effectiveSelectedId} onSelect={setSelectedId} />
                            </Panel>
                            {selectedRecord && <RiskManagerCaseDetail record={selectedRecord} />}
                        </Box>
                    )}
                    {(areaId === "business-services") && <ServiceView records={records} />}
                    {(areaId === "business-impact") && <BusinessImpactView records={records.slice(0, 20)} />}
                    {workflowFields && (
                        <Panel component="section">
                            <Stack spacing={2}>
                                <Alert severity="warning">This governance workflow has no authoritative source yet. PredatorAI will not infer or fabricate these claims.</Alert>
                                {workflowFields.map((field) => (
                                    <Stack key={field} direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                                        <Typography>{field}</Typography>
                                        <Chip label="NOT AVAILABLE" color="warning" variant="outlined" size="small" />
                                    </Stack>
                                ))}
                                <Divider />
                                <Typography variant="body2" color="text.secondary">The underlying technical and business risk context remains available in the Risk Register while this governance source is missing.</Typography>
                            </Stack>
                        </Panel>
                    )}
                </>
            )}
        </Stack>
    );
}
