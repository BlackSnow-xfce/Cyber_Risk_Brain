import type { ReactNode } from "react";

import Box from "@mui/material/Box";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type {
    ExploitationEvidence,
    ThreatIntelligenceFact,
    VulnerabilityThreatIntelligence,
} from "../ThreatIntelligence";

interface ThreatIntelligenceResultProps {
    intelligence: VulnerabilityThreatIntelligence;
}

export default function ThreatIntelligenceResult({
    intelligence,
}: ThreatIntelligenceResultProps) {
    return (
        <Stack spacing={2} aria-label="Threat intelligence result">
            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={1}
                sx={{ alignItems: { md: "center" }, justifyContent: "space-between" }}
            >
                <Box>
                    <Typography variant="overline" color="secondary.light">
                        Vulnerability intelligence
                    </Typography>
                    <Typography variant="h5">{intelligence.cve_identifier}</Typography>
                </Box>
                <Chip
                    label={`Contract ${intelligence.contract_version}`}
                    variant="outlined"
                />
            </Stack>

            <FactPanel title="NVD" fact={intelligence.nvd}>
                {intelligence.nvd.value && (
                    <FieldList
                        fields={[
                            ["Summary", intelligence.nvd.value.summary],
                            ["Published", intelligence.nvd.value.published_at],
                            ["Last modified", intelligence.nvd.value.last_modified_at],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="CVSS" fact={intelligence.cvss}>
                {intelligence.cvss.value && (
                    <FieldList
                        fields={[
                            ["Base score", String(intelligence.cvss.value.base_score)],
                            ["Severity", intelligence.cvss.value.severity],
                            ["Version", intelligence.cvss.value.version],
                            ["Vector", intelligence.cvss.value.vector],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="EPSS" fact={intelligence.epss}>
                {intelligence.epss.value && (
                    <FieldList
                        fields={[
                            ["Probability", String(intelligence.epss.value.probability)],
                            [
                                "Percentile",
                                intelligence.epss.value.percentile === null
                                    ? null
                                    : String(intelligence.epss.value.percentile),
                            ],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel title="CISA KEV" fact={intelligence.cisa_kev}>
                {intelligence.cisa_kev.value && (
                    <FieldList
                        fields={[
                            [
                                "Catalog membership",
                                intelligence.cisa_kev.value.known_exploited
                                    ? "Yes (true)"
                                    : "No (false)",
                            ],
                            ["Date added", intelligence.cisa_kev.value.date_added],
                            ["Due date", intelligence.cisa_kev.value.due_date],
                            [
                                "Required action",
                                intelligence.cisa_kev.value.required_action,
                            ],
                        ]}
                    />
                )}
            </FactPanel>

            <FactPanel
                title="Exploitation Evidence"
                fact={intelligence.exploitation_evidence}
            >
                {intelligence.exploitation_evidence.value?.map((evidence) => (
                    <EvidenceItem
                        key={`${evidence.evidence_type}:${evidence.provenance.source_reference}`}
                        evidence={evidence}
                    />
                ))}
            </FactPanel>
        </Stack>
    );
}

interface FactPanelProps {
    title: string;
    fact: ThreatIntelligenceFact<unknown>;
    children?: ReactNode;
}

function FactPanel({ title, fact, children }: FactPanelProps) {
    return (
        <Panel component="section">
            <Stack spacing={1.5}>
                <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    sx={{ alignItems: "center", flexWrap: "wrap" }}
                >
                    <Typography variant="h6">{title}</Typography>
                    <Chip label={`Status: ${fact.status}`} size="small" />
                    <Chip
                        label={`Source: ${fact.provenance.source_type}`}
                        size="small"
                        variant="outlined"
                    />
                </Stack>
                {fact.value === null ? (
                    <Typography color="text.secondary">
                        No value supplied by the backend.
                    </Typography>
                ) : (
                    children
                )}
                <Typography variant="caption" color="text.secondary">
                    Source reference: {fact.provenance.source_reference}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                    Observed at: {fact.observed_at ?? "Not provided"}
                </Typography>
            </Stack>
        </Panel>
    );
}

interface FieldListProps {
    fields: ReadonlyArray<readonly [string, string | null]>;
}

function FieldList({ fields }: FieldListProps) {
    return (
        <Stack spacing={1}>
            {fields.map(([label, value]) => (
                <Box key={label}>
                    <Typography variant="caption" color="text.secondary">
                        {label}
                    </Typography>
                    <Typography sx={{ overflowWrap: "anywhere" }}>
                        {value ?? "Not provided"}
                    </Typography>
                </Box>
            ))}
        </Stack>
    );
}

function EvidenceItem({ evidence }: { evidence: ExploitationEvidence }) {
    return (
        <Stack spacing={0.5}>
            <Typography>{evidence.evidence_type}</Typography>
            <Typography color="text.secondary">{evidence.description}</Typography>
            <Typography variant="caption" color="text.secondary">
                Evidence source: {evidence.provenance.source_type} —{" "}
                {evidence.provenance.source_reference}
            </Typography>
        </Stack>
    );
}
