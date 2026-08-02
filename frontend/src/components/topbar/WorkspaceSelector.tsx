import { useMemo, useState } from "react";

import Button from "@mui/material/Button";
import CheckIcon from "@mui/icons-material/Check";
import Divider from "@mui/material/Divider";
import Popover from "@mui/material/Popover";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";

import { useWorkspace } from "@/hooks/useWorkspace";
import { workspaceRegistry } from "@/workspaces";

export default function WorkspaceSelector() {
    const {
        workspace,
        setWorkspace,
    } = useWorkspace();

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const currentWorkspace = useMemo(
        () =>
            workspaceRegistry.find(
                (item) => item.id === workspace,
            ),
        [workspace],
    );

    return (
        <>
            <Button
                variant="outlined"
                onClick={(event) =>
                    setAnchorEl(event.currentTarget)
                }
                sx={{
                    minWidth: 300,
                    px: 2,
                    py: 1,
                    justifyContent: "space-between",
                    textTransform: "none",
                    borderRadius: 2,
                }}
            >
                <Stack
                    spacing={0.25}
                    sx={{
                        alignItems: "flex-start",
                    }}
                >
                    <Typography
                        variant="subtitle2"
                        sx={{
                            fontWeight: 700,
                        }}
                    >
                        {currentWorkspace?.name}
                    </Typography>

                    <Typography
                        variant="caption"
                        color="text.secondary"
                    >
                        {currentWorkspace?.description}
                    </Typography>
                </Stack>

                <Typography
                    variant="body2"
                    color="text.secondary"
                >
                    ▼
                </Typography>
            </Button>

            <Popover
                open={Boolean(anchorEl)}
                anchorEl={anchorEl}
                onClose={() => setAnchorEl(null)}
                anchorOrigin={{
                    vertical: "bottom",
                    horizontal: "left",
                }}
                transformOrigin={{
                    vertical: "top",
                    horizontal: "left",
                }}
                slotProps={{
                    paper: {
                        sx: {
                            mt: 1,
                            width: 360,
                            borderRadius: 3,
                            p: 1,
                        },
                    },
                }}
            >
                <Typography
                    variant="overline"
                    sx={{
                        px: 2,
                        pb: 1,
                        color: "text.secondary",
                    }}
                >
                    Switch Workspace
                </Typography>

                <Divider />

                <Stack>
                    {workspaceRegistry
                        .sort((a, b) => a.order - b.order)
                        .map((item) => {
                            const active =
                                item.id === workspace;

                            return (
                                <Button
                                    key={item.id}
                                    onClick={() => {
                                        if (!item.enabled) {
                                            return;
                                        }

                                        setWorkspace(item.id);
                                        setAnchorEl(null);
                                    }}
                                    sx={{
                                        px: 2,
                                        py: 1.5,
                                        justifyContent:
                                            "space-between",
                                        textTransform: "none",
                                        borderRadius: 2,
                                        color:
                                            "text.primary",
                                    }}
                                >
                                    <Stack
                                        spacing={0.25}
                                        sx={{
                                            alignItems:
                                                "flex-start",
                                        }}
                                    >
                                        <Typography
                                            variant="subtitle2"
                                            sx={{
                                                fontWeight: 600,
                                            }}
                                        >
                                            {item.name}
                                        </Typography>

                                        <Typography
                                            variant="caption"
                                            color="text.secondary"
                                        >
                                            {item.description}
                                        </Typography>

                                        {!item.enabled && (
                                            <Typography
                                                variant="caption"
                                                color="warning.main"
                                            >
                                                Coming soon
                                            </Typography>
                                        )}
                                    </Stack>

                                    {active && (
                                        <CheckIcon
                                            fontSize="small"
                                        />
                                    )}
                                </Button>
                            );
                        })}
                </Stack>
            </Popover>
        </>
    );
}