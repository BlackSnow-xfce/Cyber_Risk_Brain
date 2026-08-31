import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import CircularProgress from "@mui/material/CircularProgress";
import Divider from "@mui/material/Divider";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import type { FindingRiskContext } from "./FindingRiskContext";

interface FindingRiskContextSectionProps {
    context: FindingRiskContext | null;
    error: string | null;
    loading: boolean;
    onLoad: () => void;
}

export default function FindingRiskContextSection({
    context,
    error,
    loading,
    onLoad,
}: FindingRiskContextSectionProps) {
    return (
        <Stack spacing={1.5} aria-label="Finding risk context">
            <Divider />
            <Stack direction="row" sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <Typography variant="h6">Authoritative Risk Context</Typography>
                <Button size="small" variant="outlined" onClick={onLoad} disabled={loading}>
                    {loading ? "Loading" : "Load risk context"}
                </Button>
            </Stack>
            {loading && <CircularProgress size={18} />}
            {error && <Alert severity="error">{error}</Alert>}
            {context && (
                <Stack spacing={1.5}>
                    <Typography variant="subtitle2">What PredatorAI knows</Typography>
                    {context.source_facts.map((fact) => (
                        <Stack key={fact.name} spacing={0.25}>
                            <Typography variant="body2">{fact.name}: {fact.value}</Typography>
                            <Typography variant="caption" color="text.secondary">
                                Source: {fact.source_reference}
                            </Typography>
                        </Stack>
                    ))}
                    {context.asset_context.status === "resolved" && (
                        <Typography variant="body2">
                            Canonical asset {context.asset_context.canonical_asset_id}; criticality {context.asset_context.criticality}. Source: {context.asset_context.source_reference}
                        </Typography>
                    )}
                    {context.business_context && context.business_impact_readiness && <>
                    <Typography variant="subtitle2">Authoritative business context</Typography>
                    {context.business_context.status === "RESOLVED" ? (
                        <Stack spacing={0.25}>
                            {context.business_impact_readiness.facts.map((fact) => (
                                <Typography key={fact.name} variant="body2">
                                    {fact.name}: {fact.value}. Source: {fact.source_reference}
                                </Typography>
                            ))}
                        </Stack>
                    ) : (
                        <Alert severity="warning">
                            Business context {context.business_context.status}. No organizational facts were inferred.
                        </Alert>
                    )}
                    <Typography variant="subtitle2">Business-impact readiness</Typography>
                    <Typography variant="body2">
                        {context.business_impact_readiness.status}: {context.business_impact_readiness.reason}
                    </Typography>
                    {context.business_impact_readiness.missing_requirements.map((requirement) => (
                        <Typography key={requirement} variant="body2">
                            Business-impact requirement: {requirement}
                        </Typography>
                    ))}
                    </>}
                    <Typography variant="subtitle2">Threat intelligence</Typography>
                    {context.threat_intelligence.relationships.map((relationship, index) => (
                        <Stack
                            key={relationship.cve_identifier ?? `not-applicable-${index}`}
                            spacing={0.25}
                        >
                            <Typography variant="body2">
                                {relationship.cve_identifier ?? "No applicable CVE"}: {relationship.applicability}
                            </Typography>
                            {relationship.intelligence && Object.entries({
                                nvd: relationship.intelligence.nvd,
                                cvss: relationship.intelligence.cvss,
                                epss: relationship.intelligence.epss,
                                cisa_kev: relationship.intelligence.cisa_kev,
                                exploitation_evidence: relationship.intelligence.exploitation_evidence,
                            }).map(([name, fact]) => (
                                <Typography key={name} variant="caption" color="text.secondary">
                                    {name}: {fact.status}. Source: {fact.provenance.source_type} / {fact.provenance.source_reference}
                                </Typography>
                            ))}
                        </Stack>
                    ))}
                    <Typography variant="body2">
                        Correlation: {context.correlation.completeness_status}. Source: {context.correlation.source_type} / {context.correlation.source_reference}
                    </Typography>
                    {context.evidence.map((evidence) => (
                        <Stack key={evidence.identifier} spacing={0.25}>
                            <Typography variant="body2">Evidence {evidence.identifier} ({evidence.kind}, {evidence.evidence_type}, v{evidence.contract_version})</Typography>
                            <Typography variant="caption" color="text.secondary">Source: {evidence.source_type} / {evidence.source_reference}</Typography>
                            {evidence.input_references.map((reference) => (
                                <Typography key={reference} variant="caption" color="text.secondary">Input: {reference}</Typography>
                            ))}
                        </Stack>
                    ))}
                    <Typography variant="subtitle2">Information still missing</Typography>
                    {context.assessment.missing_inputs.map((input) => (
                        <Typography key={input.name} variant="body2">{input.name}: {input.state}</Typography>
                    ))}
                    {context.evidence_readiness.missing_requirements.map((requirement) => (
                        <Typography key={requirement} variant="body2">Evidence requirement: {requirement}</Typography>
                    ))}
                    <Typography variant="subtitle2">Finding risk priority</Typography>
                    {context.priority?.status === "PRIORITIZED" ? (
                        <Stack spacing={0.25}>
                            <Typography variant="body2">
                                Priority: {context.priority.band}; gated score: {context.priority.score}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                {context.priority.reason} Source: {context.priority.source_type} / {context.priority.source_reference}
                            </Typography>
                            {context.priority.considered_evidence_ids.map((identifier) => (
                                <Typography key={identifier} variant="caption" color="text.secondary">
                                    Evidence: {identifier}
                                </Typography>
                            ))}
                        </Stack>
                    ) : (
                        <Alert severity="warning">
                            Priority unavailable. {context.priority?.reason} Band and score are not available.
                        </Alert>
                    )}
                    {context.assessment.status === "INSUFFICIENT_CONTEXT" && (
                        <Alert severity="warning">
                            PredatorAI refuses to calculate risk, priority, business impact, a decision, or recommendations. {context.refusal_reason} Score, priority, business impact, decision, and recommendations are not available.
                        </Alert>
                    )}
                </Stack>
            )}
        </Stack>
    );
}
