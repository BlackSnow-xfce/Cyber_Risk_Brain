import ArrowDownwardIcon from "@mui/icons-material/ArrowDownward";
import Box from "@mui/material/Box";

export default function PipelineConnector() {
    return (
        <Box
            aria-hidden="true"
            sx={{
                display: "flex",
                justifyContent: "center",
                color: "text.secondary",
            }}
        >
            <ArrowDownwardIcon fontSize="small" />
        </Box>
    );
}
