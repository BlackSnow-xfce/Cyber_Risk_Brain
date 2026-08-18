import { useState } from "react";

import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Divider from "@mui/material/Divider";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Typography from "@mui/material/Typography";

import { useWorkspace } from "@/hooks/useWorkspace";
import { WorkspaceId } from "@/types/workspace";
import { workspaceRegistry } from "@/workspaces";

const workspaceColors: Record<WorkspaceId, string> = {
    [WorkspaceId.DECISION_CENTER]: "#4caf50",
    [WorkspaceId.THREAT_HUNTING]: "#fb8c00",
    [WorkspaceId.THREAT_INTELLIGENCE]: "#ab47bc",
    [WorkspaceId.INCIDENT_RESPONSE]: "#ef5350",
    [WorkspaceId.EXECUTIVE]: "#fbc02d",
    [WorkspaceId.RISK_MANAGEMENT]: "#42a5f5",
    [WorkspaceId.ADMINISTRATION]: "#90a4ae",
};

const workspaceGroups = [
    {
        title: "Security",
        workspaceIds: [
            WorkspaceId.DECISION_CENTER,
            WorkspaceId.THREAT_HUNTING,
            WorkspaceId.THREAT_INTELLIGENCE,
            WorkspaceId.INCIDENT_RESPONSE,
        ],
    },
    {
        title: "Management",
        workspaceIds: [
            WorkspaceId.EXECUTIVE,
            WorkspaceId.RISK_MANAGEMENT,
        ],
    },
    {
        title: "Platform",
        workspaceIds: [
            WorkspaceId.ADMINISTRATION,
        ],
    },
];

export default function WorkspaceSwitcher() {
    const {
        workspace,
        setWorkspace,
    } = useWorkspace();

    const [anchorEl, setAnchorEl] =
        useState<HTMLElement | null>(null);

    const enabledWorkspaces = workspaceRegistry
        .filter((item) => item.enabled)
        .sort((left, right) => left.order - right.order);

    const currentWorkspace =
        enabledWorkspaces.find(
            (item) => item.id === workspace,
        ) ?? enabledWorkspaces[0];

    const open = Boolean(anchorEl);

    if (!currentWorkspace) {
        return null;
    }

    return (
        <>
            <Button
                variant="outlined"
                aria-haspopup="menu"
                aria-expanded={open ? "true" : undefined}
                onClick={(event) => {
                    setAnchorEl(event.currentTarget);
                }}
                sx={{
                    minWidth: 280,
                    px: 1.5,
                    py: 0.75,
                    borderRadius: 2,
                    borderColor: "divider",
                    textTransform: "none",
                    justifyContent: "space-between",
                    color: "text.primary",
                    "&:hover": {
                        borderColor: "text.secondary",
                        backgroundColor: "action.hover",
                    },
                }}
            >
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        minWidth: 0,
                    }}
                >
                    <Box
                        aria-hidden="true"
                        sx={{
                            width: 10,
                            height: 10,
                            mr: 1.25,
                            flexShrink: 0,
                            borderRadius: "50%",
                            backgroundColor:
                                workspaceColors[
                                    currentWorkspace.id
                                ],
                            boxShadow:
                                "0 0 0 3px rgba(255, 255, 255, 0.06)",
                        }}
                    />

                    <Box
                        sx={{
                            minWidth: 0,
                            textAlign: "left",
                        }}
                    >
                        <Typography
                            component="div"
                            sx={{
                                fontSize: "0.875rem",
                                fontWeight: 600,
                                lineHeight: 1.25,
                                color: "text.primary",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                            }}
                        >
                            {currentWorkspace.name}
                        </Typography>

                        <Typography
                            component="div"
                            sx={{
                                mt: 0.25,
                                fontSize: "0.72rem",
                                lineHeight: 1.2,
                                color: "text.secondary",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                whiteSpace: "nowrap",
                            }}
                        >
                            {currentWorkspace.description}
                        </Typography>
                    </Box>
                </Box>

                <Typography
                    component="span"
                    aria-hidden="true"
                    sx={{
                        ml: 2,
                        flexShrink: 0,
                        fontSize: "0.8rem",
                        lineHeight: 1,
                        color: "text.secondary",
                        transform: open
                            ? "rotate(180deg)"
                            : "rotate(0deg)",
                        transition: "transform 160ms ease",
                    }}
                >
                    ▾
                </Typography>
            </Button>

            <Menu
                anchorEl={anchorEl}
                open={open}
                onClose={() => {
                    setAnchorEl(null);
                }}
                slotProps={{
                    paper: {
                        sx: {
                            mt: 1,
                            width: 340,
                            maxHeight: 520,
                            borderRadius: 2.5,
                            border: "1px solid",
                            borderColor: "divider",
                            backgroundImage: "none",
                            boxShadow:
                                "0 18px 48px rgba(0, 0, 0, 0.32)",
                        },
                    },
                    list: {
                        sx: {
                            py: 1,
                        },
                    },
                }}
            >
                <Typography
                    component="div"
                    sx={{
                        px: 2,
                        pt: 0.75,
                        pb: 1.25,
                        fontSize: "0.7rem",
                        fontWeight: 700,
                        letterSpacing: "0.08em",
                        textTransform: "uppercase",
                        color: "text.secondary",
                    }}
                >
                    Select workspace
                </Typography>

                {workspaceGroups.map(
                    (group, groupIndex) => {
                        const groupWorkspaces =
                            enabledWorkspaces.filter(
                                (item) =>
                                    group.workspaceIds.includes(
                                        item.id,
                                    ),
                            );

                        if (groupWorkspaces.length === 0) {
                            return null;
                        }

                        return (
                            <Box key={group.title}>
                                {groupIndex > 0 && (
                                    <Divider
                                        sx={{
                                            my: 1,
                                        }}
                                    />
                                )}

                                <Typography
                                    component="div"
                                    sx={{
                                        px: 2,
                                        py: 0.75,
                                        fontSize: "0.68rem",
                                        fontWeight: 700,
                                        letterSpacing:
                                            "0.08em",
                                        textTransform:
                                            "uppercase",
                                        color: "text.secondary",
                                    }}
                                >
                                    {group.title}
                                </Typography>

                                {groupWorkspaces.map(
                                    (item) => {
                                        const selected =
                                            item.id ===
                                            workspace;

                                        return (
                                            <MenuItem
                                                key={item.id}
                                                selected={
                                                    selected
                                                }
                                                onClick={() => {
                                                    setWorkspace(
                                                        item.id,
                                                    );
                                                    setAnchorEl(
                                                        null,
                                                    );
                                                }}
                                                sx={{
                                                    mx: 1,
                                                    px: 1.5,
                                                    py: 1.1,
                                                    minHeight: 56,
                                                    borderRadius: 1.5,
                                                    "&.Mui-selected":
                                                        {
                                                            backgroundColor:
                                                                "action.selected",
                                                        },
                                                    "&.Mui-selected:hover":
                                                        {
                                                            backgroundColor:
                                                                "action.selected",
                                                        },
                                                }}
                                            >
                                                <Box
                                                    sx={{
                                                        display:
                                                            "flex",
                                                        alignItems:
                                                            "center",
                                                        width: "100%",
                                                        minWidth: 0,
                                                    }}
                                                >
                                                    <Box
                                                        aria-hidden="true"
                                                        sx={{
                                                            width: 10,
                                                            height: 10,
                                                            mr: 1.5,
                                                            flexShrink: 0,
                                                            borderRadius:
                                                                "50%",
                                                            backgroundColor:
                                                                workspaceColors[
                                                                    item
                                                                        .id
                                                                ],
                                                            opacity:
                                                                selected
                                                                    ? 1
                                                                    : 0.7,
                                                        }}
                                                    />

                                                    <Box
                                                        sx={{
                                                            minWidth: 0,
                                                            flexGrow: 1,
                                                        }}
                                                    >
                                                        <Typography
                                                            component="div"
                                                            sx={{
                                                                fontSize:
                                                                    "0.875rem",
                                                                fontWeight:
                                                                    selected
                                                                        ? 600
                                                                        : 500,
                                                                lineHeight: 1.25,
                                                                color: "text.primary",
                                                            }}
                                                        >
                                                            {
                                                                item.name
                                                            }
                                                        </Typography>

                                                        <Typography
                                                            component="div"
                                                            sx={{
                                                                mt: 0.25,
                                                                fontSize:
                                                                    "0.72rem",
                                                                lineHeight: 1.25,
                                                                color: "text.secondary",
                                                            }}
                                                        >
                                                            {
                                                                item.description
                                                            }
                                                        </Typography>
                                                    </Box>

                                                    {selected && (
                                                        <Typography
                                                            component="span"
                                                            sx={{
                                                                ml: 1.5,
                                                                flexShrink: 0,
                                                                fontSize:
                                                                    "0.7rem",
                                                                fontWeight: 700,
                                                                letterSpacing:
                                                                    "0.06em",
                                                                textTransform:
                                                                    "uppercase",
                                                                color: "text.secondary",
                                                            }}
                                                        >
                                                            Active
                                                        </Typography>
                                                    )}
                                                </Box>
                                            </MenuItem>
                                        );
                                    },
                                )}
                            </Box>
                        );
                    },
                )}
            </Menu>
        </>
    );
}
