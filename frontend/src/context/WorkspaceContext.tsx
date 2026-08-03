import {
    createContext,
    useCallback,
    useMemo,
    useState,
    type PropsWithChildren,
} from "react";

import { WorkspaceId } from "@/types/workspace";

export interface WorkspaceContextValue {
    workspace: WorkspaceId;

    setWorkspace: (workspace: WorkspaceId) => void;

    activeNavigationItemId: string | null;

    setActiveNavigationItemId: (itemId: string) => void;
}

export const WorkspaceContext =
    createContext<WorkspaceContextValue | null>(null);

export function WorkspaceProvider({
    children,
}: PropsWithChildren) {
    const [workspace, setWorkspaceState] = useState(
        WorkspaceId.DECISION_CENTER,
    );
    const [activeNavigationItemId, setActiveNavigationItemId] =
        useState<string | null>(null);

    const setWorkspace = useCallback((nextWorkspace: WorkspaceId) => {
        setWorkspaceState(nextWorkspace);
        setActiveNavigationItemId(null);
    }, []);

    const value = useMemo(
        () => ({
            workspace,
            setWorkspace,
            activeNavigationItemId,
            setActiveNavigationItemId,
        }),
        [workspace, setWorkspace, activeNavigationItemId],
    );

    return (
        <WorkspaceContext.Provider value={value}>
            {children}
        </WorkspaceContext.Provider>
    );
}
