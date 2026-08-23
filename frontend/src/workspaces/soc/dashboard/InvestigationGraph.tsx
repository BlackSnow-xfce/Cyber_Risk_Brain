import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { ArrowRight, Bug, Database, Server, Siren, type LucideIcon } from "lucide-react";

import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

export default function InvestigationGraph({
    finding,
    incident,
    onFinding,
    onThreatIntelligence,
    onIncident,
}: {
    finding: FindingSummary | null;
    incident: FindingIncidentReference | null;
    onFinding: (id: string) => void;
    onThreatIntelligence: (id: string) => void;
    onIncident: (id: string) => void;
}) {
    const cve = finding?.title.match(/CVE-\d{4}-\d+/i)?.[0] ?? null;
    const nodes: Array<{ label: string; value: string; status: string; icon: LucideIcon; onClick?: () => void }> = [
        { label: "Finding", value: finding?.title ?? "No finding", status: "KNOWN", icon: Bug, onClick: finding ? () => onFinding(finding.id) : undefined },
        { label: "Threat intelligence / CVE", value: cve ?? "Identifier unavailable", status: cve ? "RELATED" : "NOT AVAILABLE", icon: Database, onClick: finding && cve ? () => onThreatIntelligence(finding.id) : undefined },
        { label: "Canonical asset", value: finding?.asset ?? "Asset unavailable", status: finding ? "BOUND" : "NOT AVAILABLE", icon: Server },
        { label: "Incident", value: incident?.incident_id ?? "No incident", status: incident ? "LINKED" : "NOT AVAILABLE", icon: Siren, onClick: incident ? () => onIncident(incident.incident_id) : undefined },
    ];
    return (
        <Box component="section" aria-label="Investigation path" sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1.5, p: 0.9, background: "linear-gradient(135deg, rgba(23,37,61,.9), rgba(14,22,36,.96))" }}>
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center", mb: 0.55 }}>
                <Box><Typography variant="subtitle2" sx={{ fontWeight: 800 }}>Investigation graph</Typography><Typography variant="caption" color="text.secondary">Known PredatorAI relationships — not an attack map</Typography></Box>
                <Chip label={finding ? "RELATED CONTEXT" : "NO CONTEXT"} size="small" variant="outlined" />
            </Stack>
            <Stack direction={{ xs: "column", md: "row" }} spacing={0.35} sx={{ alignItems: "center", justifyContent: "center" }}>
                {nodes.map((node, index) => <Stack key={node.label} direction={{ xs: "column", md: "row" }} spacing={0.35} sx={{ alignItems: "center", flex: 1, minWidth: 0 }}>
                    <Box component={node.onClick ? "button" : "article"} type={node.onClick ? "button" : undefined} onClick={node.onClick} sx={{ width: { xs: "100%", md: 132 }, minHeight: 76, textAlign: "center", color: "inherit", font: "inherit", border: "1px solid", borderColor: node.onClick ? "primary.main" : "divider", borderRadius: "50%", background: "radial-gradient(circle at 35% 25%, rgba(40,75,120,.75), rgba(8,15,28,.92))", p: 0.65, cursor: node.onClick ? "pointer" : "default", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", boxShadow: node.onClick ? "0 0 0 2px rgba(55,145,255,.12)" : "none" }}>
                        <node.icon size={16} /><Typography variant="overline" color="text.secondary" sx={{ lineHeight: 1.1, mt: 0.25 }}>{node.label}</Typography>
                        <Typography variant="caption" sx={{ fontWeight: 700, overflowWrap: "anywhere", maxWidth: 132, mt: 0.3 }}>{node.value}</Typography>
                        <Typography variant="caption" color="primary.main" sx={{ fontWeight: 800, lineHeight: 1.1, mt: 0.2 }}>{node.status}</Typography>
                    </Box>
                    {index < nodes.length - 1 && <Stack spacing={0.05} sx={{ alignItems: "center", minWidth: 34 }}><Typography variant="caption" color="text.secondary" sx={{ fontSize: "0.58rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>related</Typography><ArrowRight size={22} aria-hidden="true" color="currentColor" /></Stack>}
                </Stack>)}
            </Stack>
        </Box>
    );
}
