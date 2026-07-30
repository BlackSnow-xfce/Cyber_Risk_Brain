import PlatformLayout from "./platform/layout/PlatformLayout";
import WorkspaceOutlet from "./platform/workspace/WorkspaceOutlet";

function App() {
    return (
        <PlatformLayout>
            <WorkspaceOutlet />
        </PlatformLayout>
    );
}

export default App;