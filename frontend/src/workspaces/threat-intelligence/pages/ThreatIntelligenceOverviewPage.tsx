import Box from "@mui/material/Box";
import Alert from "@mui/material/Alert";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import { useEffect, useState } from "react";

import IntelligenceStateCard from "./IntelligenceStateCard";
import ThreatIntelligencePageHeader from "./ThreatIntelligencePageHeader";
import type { FindingSummary } from "@/workspaces/soc/findings/FindingSummary";
import { getFindings } from "@/workspaces/soc/findings/FindingsApiClient";

interface ThreatIntelligenceOverviewPageProps {
    loadFindings?: () => Promise<readonly FindingSummary[]>;
}

export default function ThreatIntelligenceOverviewPage({ loadFindings = getFindings }: ThreatIntelligenceOverviewPageProps) {
    const [findings, setFindings] = useState<readonly FindingSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        let active = true;
        loadFindings().then((result) => {
            if (active) setFindings(result);
        }).catch(() => {
            if (active) setError(true);
        }).finally(() => {
            if (active) setLoading(false);
        });
        return () => { active = false; };
    }, [loadFindings]);

    const overviewSections = [
        { title: "Findings in environment", description: loading ? "Loading live findings…" : error ? "Live findings are unavailable." : `${findings.length} findings loaded from PredatorAI.`, status: loading ? "Loading" : error ? "Unavailable" : "Available" },
        { title: "CVE / vulnerability intelligence", description: "Resolve an exact CVE in Explorer or open a finding-scoped TI view.", status: "On demand" },
        { title: "NVD / CVSS / EPSS / CISA KEV", description: "Displayed when returned by the vulnerability intelligence contract.", status: "Source-backed" },
        { title: "Provenance and completeness", description: "Each returned fact retains source and availability metadata.", status: "Preserved" },
        { title: "Environment Relevance", description: "Finding relationships are shown only when the backend returns them.", status: "Not evaluated" },
        { title: "Unsupported intelligence objects", description: "Attacker, campaign, malware and IOC relationships are not connected.", status: "Not connected" },
    ];
    return (
        <Stack spacing={3}>
            <ThreatIntelligencePageHeader
                eyebrow="Analyst intelligence workspace"
                title="Threat Intelligence Overview"
                description="Assess available intelligence, its provenance and its relevance to the environment. Sources that are not connected remain explicitly visible."
            />
            <Box
                sx={{
                    display: "grid",
                    gridTemplateColumns: {
                        xs: "minmax(0, 1fr)",
                        md: "repeat(2, minmax(0, 1fr))",
                        xl: "repeat(3, minmax(0, 1fr))",
                    },
                    gap: 2,
                }}
            >
                {overviewSections.map((section) => (
                    <IntelligenceStateCard key={section.title} title={section.title} description={section.description} status={section.status} />
                ))}
            </Box>
            {loading && <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}><CircularProgress size={18} /><Typography variant="body2">Loading live environment context…</Typography></Stack>}
            {error && <Alert severity="warning">Live findings could not be loaded; no intelligence conclusion is inferred.</Alert>}
        </Stack>
    );
}
