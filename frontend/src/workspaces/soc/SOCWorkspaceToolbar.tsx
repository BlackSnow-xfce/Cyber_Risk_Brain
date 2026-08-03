import type { ReactNode } from "react";

import FilterListIcon from "@mui/icons-material/FilterList";
import RefreshIcon from "@mui/icons-material/Refresh";
import SearchIcon from "@mui/icons-material/Search";
import SortIcon from "@mui/icons-material/Sort";
import Button from "@mui/material/Button";
import InputAdornment from "@mui/material/InputAdornment";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";

import Panel from "@/ui/panel/Panel";

interface SOCWorkspaceToolbarProps {
    searchLabel: string;
    additionalControls?: ReactNode;
    showSort?: boolean;
}

export default function SOCWorkspaceToolbar({
    searchLabel,
    additionalControls,
    showSort = true,
}: SOCWorkspaceToolbarProps) {
    return (
        <Panel>
            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={2}
                sx={{ alignItems: { xs: "stretch", md: "center" } }}
            >
                <TextField
                    fullWidth
                    size="small"
                    label={searchLabel}
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

                {additionalControls}

                <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    sx={{ flexWrap: "wrap" }}
                >
                    <Button variant="outlined" startIcon={<FilterListIcon />}>
                        Filter
                    </Button>
                    {showSort && (
                        <Button variant="outlined" startIcon={<SortIcon />}>
                            Sort
                        </Button>
                    )}
                    <Button variant="outlined" startIcon={<RefreshIcon />}>
                        Refresh
                    </Button>
                </Stack>
            </Stack>
        </Panel>
    );
}
