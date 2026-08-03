import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutlined";
import HourglassEmptyIcon from "@mui/icons-material/HourglassEmpty";
import OutputOutlinedIcon from "@mui/icons-material/OutputOutlined";

export const traceIcons = {
    matched: CheckCircleOutlineIcon,
    skipped: HourglassEmptyIcon,
    generated: OutputOutlinedIcon,
} as const;
