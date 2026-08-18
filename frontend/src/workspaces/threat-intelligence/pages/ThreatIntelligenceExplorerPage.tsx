import { useState } from "react";
import type { FormEvent } from "react";

import Alert from "@mui/material/Alert";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Chip from "@mui/material/Chip";
import CircularProgress from "@mui/material/CircularProgress";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import Typography from "@mui/material/Typography";

import Panel from "@/ui/panel/Panel";

import type { VulnerabilityThreatIntelligence } from "../ThreatIntelligence";
import {
    getVulnerabilityThreatIntelligence,
    ThreatIntelligenceRequestError,
} from "../ThreatIntelligenceApiClient";
import ThreatIntelligencePageHeader from "./ThreatIntelligencePageHeader";
import ThreatIntelligenceResult from "./ThreatIntelligenceResult";

const intelligenceTypes = [
    { name: "IOC", status: "Capability unavailable", detail: "No IOC ingestion or query contract exists." },
    { name: "IP", status: "Capability unavailable", detail: "No IP intelligence provider is connected." },
    { name: "Domain", status: "Capability unavailable", detail: "No domain intelligence provider is connected." },
    { name: "Hash", status: "Capability unavailable", detail: "No hash intelligence provider is connected." },
    { name: "Threat Actor", status: "Capability unavailable", detail: "Threat-actor ingestion is outside the current scope." },
    { name: "Malware", status: "Capability unavailable", detail: "Malware feeds are outside the current scope." },
    { name: "Campaign", status: "Capability unavailable", detail: "Campaign ingestion is outside the current scope." },
];

interface ThreatIntelligenceExplorerPageProps {
    lookup?: (cveIdentifier: string) => Promise<VulnerabilityThreatIntelligence>;
}

export default function ThreatIntelligenceExplorerPage({
    lookup = getVulnerabilityThreatIntelligence,
}: ThreatIntelligenceExplorerPageProps) {
    const [cveIdentifier, setCveIdentifier] = useState("");
    const [result, setResult] = useState<VulnerabilityThreatIntelligence | null>(
        null,
    );
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);

    const submit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        const requestedCve = cveIdentifier.trim();
        if (!requestedCve || loading) return;

        setLoading(true);
        setError(null);
        setResult(null);
        try {
            setResult(await lookup(requestedCve));
        } catch (requestError) {
            setError(errorMessage(requestError));
        } finally {
            setLoading(false);
        }
    };

    return (
        <Stack spacing={3}>
            <ThreatIntelligencePageHeader
                eyebrow="Intelligence research"
                title="Threat Intelligence Explorer"
                description="Look up an exact CVE identifier through the PredatorAI backend. Results preserve source provenance and data availability from Threat Intelligence Contract 1.0."
            />

            <Panel component="section">
                <Stack component="form" spacing={2} onSubmit={submit}>
                    <Typography variant="h6">CVE lookup</Typography>
                    <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5}>
                        <TextField
                            label="CVE identifier"
                            placeholder="CVE-2021-44228"
                            value={cveIdentifier}
                            onChange={(event) => setCveIdentifier(event.target.value)}
                            disabled={loading}
                            fullWidth
                            slotProps={{
                                htmlInput: { "aria-label": "CVE identifier" },
                            }}
                        />
                        <Button
                            type="submit"
                            variant="contained"
                            disabled={loading || !cveIdentifier.trim()}
                            sx={{ minWidth: 140 }}
                        >
                            {loading ? "Loading…" : "Search"}
                        </Button>
                    </Stack>
                    {loading && (
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                            <CircularProgress size={20} />
                            <Typography>Loading threat intelligence…</Typography>
                        </Stack>
                    )}
                    {error && <Alert severity="error">{error}</Alert>}
                </Stack>
            </Panel>

            {result && <ThreatIntelligenceResult intelligence={result} />}

            <Typography variant="h6">Other intelligence objects</Typography>
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
                {intelligenceTypes.map((type) => (
                    <Panel key={type.name} component="section" sx={{ minHeight: 150 }}>
                        <Stack spacing={1.5}>
                            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between" }}>
                                <Typography variant="h6">{type.name}</Typography>
                                <Chip label={type.status} size="small" variant="outlined" />
                            </Stack>
                            <Typography variant="body2" color="text.secondary">
                                {type.detail}
                            </Typography>
                        </Stack>
                    </Panel>
                ))}
            </Box>
        </Stack>
    );
}

function errorMessage(error: unknown): string {
    if (!(error instanceof ThreatIntelligenceRequestError)) {
        return "Threat intelligence could not be loaded.";
    }
    if (error.status === null) {
        return "The PredatorAI backend is not reachable.";
    }
    if (error.status === 404) {
        return "No threat intelligence was found for this CVE.";
    }
    if (error.status === 422) {
        return "The CVE identifier is invalid.";
    }
    if (error.status === 502 || error.status === 503 || error.status === 504) {
        return "Threat intelligence sources are currently unavailable.";
    }
    return "Threat intelligence could not be loaded.";
}
