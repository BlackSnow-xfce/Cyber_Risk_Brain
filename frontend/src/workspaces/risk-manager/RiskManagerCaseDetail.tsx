import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import {
    businessService,
    evidenceStatus,
    missingEvidence,
    riskScore,
    serviceCriticality,
    technicalBand,
    type RiskManagerRecord,
} from "./RiskManagerProjection";

function Field({ label, value, muted = false }: { label: string; value: string; muted?: boolean }) {
    return (
        <Box sx={{ minWidth: 0 }}>
            <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: "0.06em" }}>
                {label}
            </Typography>
            <Typography variant="body2" color={muted ? "text.secondary" : "text.primary"} sx={{ mt: 0.25, overflowWrap: "anywhere" }}>
                {value}
            </Typography>
        </Box>
    );
}

export default function RiskManagerCaseDetail({ record }: { record: RiskManagerRecord }) {
    const context = record.context;
    const missing = missingEvidence(record);

    return (
        <Panel component="aside" sx={{ position: { xl: "sticky" }, top: { xl: 24 }, alignSelf: "start" }}>
            <Stack spacing={2}>
                <Box>
                    <Typography variant="overline" color="info.main">Risk case</Typography>
                    <Typography variant="h6" sx={{ fontWeight: 750 }}>{record.finding.title}</Typography>
                    <Typography variant="caption" color="text.secondary">{record.finding.id}</Typography>
                </Box>

                <Stack direction="row" spacing={1} useFlexGap sx={{ flexWrap: "wrap" }}>
                    <Chip label={technicalBand(record)} variant="outlined" color={technicalBand(record) === "CRITICAL" ? "error" : technicalBand(record) === "HIGH" ? "warning" : "default"} />
                    <Chip label={`Score ${riskScore(record)}`} variant="outlined" />
                    <Chip label={evidenceStatus(record)} variant="outlined" color={evidenceStatus(record) === "READY" ? "success" : "warning"} />
                </Stack>

                <Divider />

                <Box sx={{ display: "grid", gridTemplateColumns: "repeat(2,minmax(0,1fr))", gap: 1.5 }}>
                    <Field label="Observed asset" value={record.finding.asset} />
                    <Field label="Canonical asset" value={context?.asset_context.canonical_asset_id ?? "NOT AVAILABLE"} />
                    <Field label="Business service" value={businessService(record)} />
                    <Field label="Service criticality" value={serviceCriticality(record)} />
                    <Field label="Environment" value={context?.business_context?.environment ?? "NOT AVAILABLE"} />
                    <Field label="Scanner severity" value={record.finding.vendorSeverity} />
                </Box>

                <Divider />

                <Box>
                    <Typography variant="subtitle2">Why PredatorAI considers this dangerous</Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 0.75 }}>
                        {context?.priority?.reason ?? context?.refusal_reason ?? "No authoritative risk assessment is available for this finding."}
                    </Typography>
                </Box>

                {context?.technical_effect?.effects.length ? (
                    <Box>
                        <Typography variant="subtitle2" sx={{ mb: 1 }}>Technical effect</Typography>
                        <Stack spacing={1}>
                            {context.technical_effect.effects.map((effect) => (
                                <Box key={`${effect.cve_identifier}:${effect.source_reference}`} sx={{ p: 1.25, border: "1px solid", borderColor: "divider", borderRadius: 1.5 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 700 }}>{effect.cve_identifier}</Typography>
                                    <Typography variant="caption" color="text.secondary">C {effect.confidentiality} · I {effect.integrity} · A {effect.availability}</Typography>
                                    <Typography variant="caption" color="text.secondary" display="block" sx={{ overflowWrap: "anywhere" }}>{effect.source_reference}</Typography>
                                </Box>
                            ))}
                        </Stack>
                    </Box>
                ) : null}

                <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Evidence & provenance</Typography>
                    <Stack spacing={0.75}>
                        <Field label="Risk source" value={context?.priority?.source_reference ?? "NOT AVAILABLE"} muted />
                        <Field label="Asset source" value={context?.asset_context.source_reference ?? "NOT AVAILABLE"} muted />
                        <Field label="Business source" value={context?.business_context?.source_reference ?? "NOT AVAILABLE"} muted />
                        <Field label="Correlation source" value={context?.correlation.source_reference ?? "NOT AVAILABLE"} muted />
                    </Stack>
                </Box>

                <Box>
                    <Typography variant="subtitle2" sx={{ mb: 1 }}>Governance readiness</Typography>
                    <Stack spacing={0.75}>
                        {missing.length > 0 ? missing.map((item) => (
                            <Typography key={item} variant="body2" color="warning.main">• {item}</Typography>
                        )) : <Typography variant="body2" color="success.main">Risk assessment evidence complete</Typography>}
                        {['Owner', 'Treatment', 'Risk acceptance', 'SLA / deadline', 'Escalation'].map((item) => (
                            <Stack key={item} direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                                <Typography variant="body2">{item}</Typography>
                                <Chip label="NOT AVAILABLE" size="small" variant="outlined" color="warning" />
                            </Stack>
                        ))}
                    </Stack>
                </Box>
            </Stack>
        </Panel>
    );
}
