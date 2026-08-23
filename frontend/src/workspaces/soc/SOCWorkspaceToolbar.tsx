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
    searchValue?: string;
    onSearchChange?: (value: string) => void;
    onRefresh?: () => void;
    refreshing?: boolean;
    additionalControls?: ReactNode;
    showFilter?: boolean;
    showSort?: boolean;
    compact?: boolean;
}

export default function SOCWorkspaceToolbar({
    searchLabel,
    searchValue = "",
    onSearchChange,
    onRefresh,
    refreshing = false,
    additionalControls,
    showFilter = false,
    showSort = false,
    compact = false,
}: SOCWorkspaceToolbarProps) {
    return (
        <Panel sx={compact ? { p: 0.75, borderRadius: 1.5 } : undefined}>
            <Stack
                direction={{ xs: "column", md: "row" }}
                spacing={compact ? 0.75 : 2}
                sx={{ alignItems: { xs: "stretch", md: "center" } }}
            >
                <TextField
                    fullWidth
                    size="small"
                    label={searchLabel}
                    value={searchValue}
                    onChange={(event) => onSearchChange?.(event.target.value)}
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
                    {showFilter && (
                        <Button variant="outlined" startIcon={<FilterListIcon />} disabled>
                            Filter
                        </Button>
                    )}
                    {showSort && (
                        <Button variant="outlined" startIcon={<SortIcon />}>
                            Sort
                        </Button>
                    )}
                    {onRefresh && (
                        <Button
                            variant="outlined"
                            startIcon={<RefreshIcon />}
                            onClick={onRefresh}
                            disabled={refreshing}
                        >
                            {refreshing ? "Refreshing" : "Refresh"}
                        </Button>
                    )}
                </Stack>
            </Stack>
        </Panel>
    );
}
