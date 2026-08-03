import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import AutoAwesomeMotionOutlinedIcon from "@mui/icons-material/AutoAwesomeMotionOutlined";
import FactCheckOutlinedIcon from "@mui/icons-material/FactCheckOutlined";
import HubOutlinedIcon from "@mui/icons-material/HubOutlined";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import PsychologyOutlinedIcon from "@mui/icons-material/PsychologyOutlined";
import RuleOutlinedIcon from "@mui/icons-material/RuleOutlined";
import TaskAltOutlinedIcon from "@mui/icons-material/TaskAltOutlined";

export const pipelineIcons = {
    knowledge: AutoAwesomeMotionOutlinedIcon,
    knowledgeBinding: AccountTreeOutlinedIcon,
    evidence: FactCheckOutlinedIcon,
    correlation: HubOutlinedIcon,
    inference: LightbulbOutlinedIcon,
    reasoning: PsychologyOutlinedIcon,
    decision: RuleOutlinedIcon,
    recommendation: TaskAltOutlinedIcon,
} as const;
