import FilterListIcon from "@mui/icons-material/FilterList";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import SortIcon from "@mui/icons-material/Sort";
import Button from "@mui/material/Button";
import InputAdornment from "@mui/material/InputAdornment";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";

import Panel from "@/ui/panel/Panel";

export default function FindingsToolbar() {
    return (
        <Panel>
            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={2}
                sx={{
                    alignItems: {
                        xs: "stretch",
                        md: "center",
                    },
                }}
            >
                <TextField
                    fullWidth
                    size="small"
                    label="Search findings"
                    slotProps={{
                        input: {
                            startAdornment: (
                                <InputAdornment position="start">
                                    <SearchIcon fontSize="small" />
                                </InputAdornment>
                            ),
                        },
                    }}
                />

                <Stack direction="row" spacing={1}>
                    <Button
                        variant="outlined"
                        startIcon={<FilterListIcon />}
                    >
                        Filter
                    </Button>

                    <Button
                        variant="outlined"
                        startIcon={<SortIcon />}
                    >
                        Sort
                    </Button>

                    <Button
                        variant="outlined"
                        startIcon={<RefreshIcon />}
                    >
                        Refresh
                    </Button>
                </Stack>
            </Stack>
        </Panel>
    );
}
