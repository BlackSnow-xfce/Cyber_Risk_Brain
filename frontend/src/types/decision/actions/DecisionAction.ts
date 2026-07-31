import type {
    ActionStatus,
    ActionType,
    Priority,
} from "../enums";

export interface DecisionAction {
    id: string;

    title: string;

    description: string;

    type: ActionType;

    priority: Priority;

    status: ActionStatus;

    owner?: string;

    dueDate?: string;

    automation: boolean;

    outcome?: string;
}