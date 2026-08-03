import { useWorkspace } from "@/hooks/useWorkspace";

import SOCLayout from "./SOCLayout";
import { SOCWorkspaceProvider } from "./SOCWorkspaceContext";
import {
    defaultSOCPageId,
    isSOCPageId,
    socPageRegistry,
} from "./pages";

export default function SOCWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const activePageId = isSOCPageId(activeNavigationItemId)
        ? activeNavigationItemId
        : defaultSOCPageId;
    const ActivePage = socPageRegistry[activePageId];

    return (
        <SOCWorkspaceProvider>
            <SOCLayout>
                <ActivePage />
            </SOCLayout>
        </SOCWorkspaceProvider>
    );
}
