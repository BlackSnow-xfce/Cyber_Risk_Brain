import type { LucideIcon } from "lucide-react";

export interface NavigationItem {
    id: string;

    label: string;

    section: string;

    icon: LucideIcon;

    route: string;

    enabled?: boolean;

    badge?: string;

    children?: NavigationItem[];
}