import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";

import SOCWorkspaceToolbar from "../SOCWorkspaceToolbar";

interface ExplainabilityToolbarProps {
    entities: readonly { id: string; title: string }[];
    selectedEntityId: string;
}

export default function ExplainabilityToolbar({
    entities,
    selectedEntityId,
}: ExplainabilityToolbarProps) {
    return (
        <SOCWorkspaceToolbar
            searchLabel="Search explainability"
            showSort={false}
            additionalControls={
                <FormControl
                    size="small"
                    sx={{ minWidth: { xs: "100%", md: 220 } }}
                >
                    <InputLabel id="explainability-entity-label">
                        Entity
                    </InputLabel>
                    <Select
                        labelId="explainability-entity-label"
                        label="Entity"
                        defaultValue={selectedEntityId}
                    >
                        {entities.map((entity) => (
                            <MenuItem key={entity.id} value={entity.id}>
                                {entity.title}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>
            }
        />
    );
}
