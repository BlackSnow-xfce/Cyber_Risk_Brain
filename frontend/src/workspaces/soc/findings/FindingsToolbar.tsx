import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";

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
        <SOCWorkspaceToolbar
            searchLabel="Search findings"
            searchValue={searchValue}
            onSearchChange={onSearchChange}
            onRefresh={onRefresh}
            refreshing={refreshing}
        />
    );
}
