import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";

interface ThreatIntelligencePageHeaderProps {
    eyebrow: string;
    title: string;
    description: string;
}

export default function ThreatIntelligencePageHeader({
    eyebrow,
    title,
    description,
}: ThreatIntelligencePageHeaderProps) {
    return (
        <Box component="header">
            <Typography variant="overline" color="secondary.light">
                {eyebrow}
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700 }}>
                {title}
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1, maxWidth: 840 }}>
                {description}
            </Typography>
        </Box>
    );
}
