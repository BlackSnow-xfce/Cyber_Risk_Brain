import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import type { FindingIncidentReference } from "../findings/FindingIncidentApiClient";
import type { FindingSummary } from "../findings/FindingSummary";

export default function PredatorAIAnalysisPanel({ finding, incident, loading }: { finding: FindingSummary | null; incident: FindingIncidentReference | null; loading: boolean }) {
    if (!finding) return <Typography color="text.secondary">No investigation context is available.</Typography>;
    const sections = [["What happened?", `${finding.title} is present for ${finding.asset}.`], ["Why this matters", `${finding.vendorSeverity} severity requires analyst investigation.`], ["What we know", `Finding and asset are known; incident is ${loading ? "loading" : incident ? "linked" : "not available"}.`], ["What is not verified", "No exploit, RCE or compromise conclusion"], ["Investigate next", "Review Finding Details, TI context and the linked Incident."]];
    return <Stack spacing={0.65}>{sections.map(([title, text]) => <Box key={title} sx={{ borderLeft: "3px solid", borderColor: title === "What is not verified" ? "warning.main" : title === "Investigate next" ? "success.main" : "primary.main", pl: 0.85, py: 0.2, background: "rgba(8,15,28,.28)" }}><Typography variant="caption" color={title === "What is not verified" ? "warning.light" : title === "Investigate next" ? "success.light" : "primary.light"} sx={{ fontWeight: 800, letterSpacing: "0.03em" }}>{title}</Typography><Typography variant="body2" sx={{ mt: 0.1, lineHeight: 1.3 }}>{text}</Typography></Box>)}</Stack>;
}
