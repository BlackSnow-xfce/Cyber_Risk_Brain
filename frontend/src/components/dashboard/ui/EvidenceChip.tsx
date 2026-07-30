import Chip from "@mui/material/Chip";

interface EvidenceChipProps {
    label: string;
}

export default function EvidenceChip({
    label,
}: EvidenceChipProps) {
    return (
        <Chip
            label={label}
            variant="outlined"
            size="small"
            sx={{
                borderRadius: 2,
                fontWeight: 600,
                borderColor: "divider",
                bgcolor: "background.default",
            }}
        />
    );
}