import Box from "@mui/material/Box";

import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";

import { findingsDensity } from "./FindingsPresentationDensity";

interface FindingsToolbarProps {
    searchValue: string;
    onSearchChange: (value: string) => void;
    onRefresh: () => void;
    refreshing: boolean;
}

export default function FindingsToolbar({
    searchValue,
    onSearchChange,
    onRefresh,
    refreshing,
}: FindingsToolbarProps) {
    return (
        <Box data-findings-density="toolbar" sx={{ "& .MuiInputBase-input, & .MuiInputLabel-root": findingsDensity.searchInput, "& .MuiButton-root": findingsDensity.toolbarButton }}>
            <SOCWorkspaceToolbar
                searchLabel="Search findings"
                searchValue={searchValue}
                onSearchChange={onSearchChange}
                onRefresh={onRefresh}
                refreshing={refreshing}
            />
        </Box>
    );
}
