import MenuItem from "@mui/material/MenuItem";
import TextField from "@mui/material/TextField";

import { useWorkspace } from "@/hooks/useWorkspace";
import { workspaceRegistry } from "@/workspaces";

export default function WorkspaceSelector() {
    const {
        workspace,
        setWorkspace,
    } = useWorkspace();

    return (
        <TextField
            select
            size="small"
            label="Workspace"
            value={workspace}
            onChange={(event) =>
                setWorkspace(event.target.value as typeof workspace)
            }
            sx={{
                minWidth: 260,
            }}
        >
            {workspaceRegistry
                .filter((workspace) => workspace.enabled)
                .map((workspace) => (
                    <MenuItem
                        key={workspace.id}
                        value={workspace.id}
                    >
                        {workspace.name}
                    </MenuItem>
                ))}
        </TextField>
    );
}