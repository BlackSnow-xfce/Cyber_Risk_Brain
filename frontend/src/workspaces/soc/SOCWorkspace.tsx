import { useLocation } from "react-router-dom";

import SOCLayout from "./SOCLayout";
import { SOCWorkspaceProvider } from "./SOCWorkspaceContext";
import {
    defaultSOCPageId,
    socPageIdFromPathname,
    socPageRegistry,
} from "./pages";

export default function SOCWorkspace() {
    const { pathname } = useLocation();
    const activePageId = socPageIdFromPathname(pathname) ?? defaultSOCPageId;
    const ActivePage = socPageRegistry[activePageId];

    return (
        <SOCWorkspaceProvider>
            <SOCLayout>
                <ActivePage />
            </SOCLayout>
        </SOCWorkspaceProvider>
    );
}
