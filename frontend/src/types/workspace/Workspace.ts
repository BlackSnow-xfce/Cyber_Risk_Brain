import { WorkspaceId } from "./WorkspaceId";

export interface Workspace {
    id: WorkspaceId;

    name: string;

    description: string;

    order: number;

    enabled: boolean;
}