import {
    createContext,
    useMemo,
    useState,
    type PropsWithChildren,
} from "react";

import { WorkspaceId } from "@/types/workspace";

export interface WorkspaceContextValue {
    workspace: WorkspaceId;

    setWorkspace: (workspace: WorkspaceId) => void;
}

export const WorkspaceContext =
    createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({
    children,
}: PropsWithChildren) {
    const [workspace, setWorkspace] = useState(
        WorkspaceId.DECISION_CENTER,
    );

    const value = useMemo(
        () => ({
            workspace,
            setWorkspace,
        }),
        [workspace],
    );

    return (
        <WorkspaceContext.Provider value={value}>
            {children}
        </WorkspaceContext.Provider>
    );
}