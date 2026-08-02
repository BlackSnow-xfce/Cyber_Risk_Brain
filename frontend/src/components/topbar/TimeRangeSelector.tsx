import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";

export default function TimeRangeSelector() {
    return (
        <TextField
            select
            size="small"
            label="Time Range"
            defaultValue="7d"
            sx={{
                minWidth: 170,
            }}
        >
            <MenuItem value="24h">
                Last 24 Hours
            </MenuItem>

            <MenuItem value="7d">
                Last 7 Days
            </MenuItem>

            <MenuItem value="30d">
                Last 30 Days
            </MenuItem>

            <MenuItem value="90d">
                Last 90 Days
            </MenuItem>
        </TextField>
    );
}