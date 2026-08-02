import { useWorkspace } from "@/hooks/useWorkspace";

import { WorkspaceId } from "@/types/workspace";

import { SOCWorkspace } from "@/workspaces/soc";
import { ExecutiveWorkspace } from "@/workspaces/executive";

export default function WorkspaceOutlet() {
    const { workspace } = useWorkspace();

    switch (workspace) {
        case WorkspaceId.DECISION_CENTER:
            return <SOCWorkspace />;

        case WorkspaceId.EXECUTIVE:
            return <ExecutiveWorkspace />;

        default:
            return <SOCWorkspace />;
    }
}