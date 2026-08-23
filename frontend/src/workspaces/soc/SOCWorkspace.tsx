import { useWorkspace } from "@/hooks/useWorkspace";
import { useLocation } from "react-router-dom";

import SOCLayout from "./SOCLayout";
import { SOCWorkspaceProvider } from "./SOCWorkspaceContext";
import {
    defaultSOCPageId,
    isSOCPageId,
    socPageIdFromPathname,
    socPageRegistry,
} from "./pages";

export default function SOCWorkspace() {
    const { activeNavigationItemId } = useWorkspace();
    const { pathname } = useLocation();
    const activePageId = isSOCPageId(activeNavigationItemId)
        ? activeNavigationItemId
        : socPageIdFromPathname(pathname) ?? defaultSOCPageId;
    const ActivePage = socPageRegistry[activePageId];

    return (
        <SOCWorkspaceProvider>
            <SOCLayout>
                <ActivePage />
            </SOCLayout>
        </SOCWorkspaceProvider>
    );
}
