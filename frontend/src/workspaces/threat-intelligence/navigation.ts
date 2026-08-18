import { Building2, LayoutDashboard, Search } from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

export const threatIntelligenceNavigation: NavigationItem[] = [
    {
        section: "Threat Intelligence",
        id: "overview",
        label: "Overview",
        route: "/threat-intelligence",
        icon: LayoutDashboard,
    },
    {
        section: "Threat Intelligence",
        id: "explorer",
        label: "Explorer",
        route: "/threat-intelligence/explorer",
        icon: Search,
    },
    {
        section: "Environment Context",
        id: "our-environment",
        label: "Our Environment",
        route: "/threat-intelligence/environment",
        icon: Building2,
    },
];
