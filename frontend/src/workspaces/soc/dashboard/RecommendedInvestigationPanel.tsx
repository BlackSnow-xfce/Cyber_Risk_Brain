import Button from "@mui/material/Button";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { BookOpen, ExternalLink, FileSearch, Siren } from "lucide-react";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

export default function RecommendedInvestigationPanel({ finding, incident, onFinding, onTi, onIncident, onCommandCenter }: { finding: FindingSummary | null; incident: FindingIncidentReference | null; onFinding: (id: string) => void; onTi: (id: string) => void; onIncident: (id: string) => void; onCommandCenter: (id: string) => void }) {
    const cve = finding?.title.match(/CVE-\d{4}-\d+/i)?.[0];
    const actions = [{ label: "Open Finding", detail: "Review the authoritative finding", icon: FileSearch, disabled: !finding, click: () => finding && onFinding(finding.id) }, { label: "Open Threat Intelligence", detail: cve ?? "No CVE identifier", icon: BookOpen, disabled: !finding || !cve, click: () => finding && onTi(finding.id) }, { label: "Open Incident", detail: incident?.incident_id ?? "No linked incident", icon: Siren, disabled: !incident, click: () => incident && onIncident(incident.incident_id) }, { label: "Open Command Center", detail: "Technical incident deep dive", icon: ExternalLink, disabled: !incident, click: () => incident && onCommandCenter(incident.incident_id) }];
    return <Stack component="section" aria-label="Recommended investigation" spacing={0.45}>{actions.map(({ label, detail, icon: Icon, disabled, click }) => <Button key={label} aria-label={label} onClick={click} disabled={disabled} variant="text" sx={{ justifyContent: "flex-start", textAlign: "left", textTransform: "none", p: 0.7, borderLeft: "2px solid", borderColor: disabled ? "divider" : "primary.main", borderRadius: 0.75, "&:hover": { backgroundColor: "rgba(55,145,255,.12)", borderColor: "primary.light" } }}><Icon size={17} /><Stack sx={{ ml: 0.8 }}><Typography variant="body2" sx={{ fontWeight: 800 }}>{label}</Typography><Typography variant="caption" color="text.secondary">{detail}</Typography></Stack></Button>)}</Stack>;
}
