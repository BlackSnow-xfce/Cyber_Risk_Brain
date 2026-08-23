import Box from "@mui/material/Box";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

export default function InvestigationContextGraph() {
    return (
        <Box component="section" aria-label="Investigation context graph" sx={{ border: "1px solid", borderColor: "divider", borderRadius: 1.5, p: 1.1 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 800 }}>Context graph</Typography>
            <Typography variant="caption" color="text.secondary">Bound relationships only</Typography>
            <Stack direction="row" spacing={1} sx={{ alignItems: "center", justifyContent: "center", mt: 1 }}>
                {[["Finding", "Known"], ["CVE / TI", "Related"], ["Asset", "Bound"], ["Incident", "Linked"]].map(([label, state], index) => (
                    <Stack key={label} direction="row" spacing={1} sx={{ alignItems: "center" }}>
                        <Box sx={{ px: 0.9, py: 0.55, borderRadius: 1, border: "1px solid", borderColor: "divider", backgroundColor: "background.default" }}><Typography variant="caption" sx={{ fontWeight: 700 }}>{label}</Typography><Typography variant="caption" color="text.secondary" sx={{ display: "block" }}>{state}</Typography></Box>
                        {index < 3 && <Typography color="text.secondary">—</Typography>}
                    </Stack>
                ))}
            </Stack>
        </Box>
    );
}
