import {
    BarChart3,
    Building2,
    Gauge,
    LayoutDashboard,
    Search,
    Shield,
    ShieldAlert,
    Target,
    Workflow,
} from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

export const socNavigation: NavigationItem[] = [
    {
        section: "Overview",
        id: "dashboard",
        label: "Dashboard",
        route: "/",
        icon: LayoutDashboard,
    },
    {
        section: "Overview",
        id: "risk-posture",
        label: "Risk Posture",
        route: "/risk-posture",
        icon: Gauge,
    },
    {
        section: "Overview",
        id: "attack-surface",
        label: "Attack Surface",
        route: "/attack-surface",
        icon: Target,
    },
    {
        section: "Detect & Analyze",
        id: "findings",
        label: "Findings",
        route: "/findings",
        icon: Search,
    },
    {
        section: "Detect & Analyze",
        id: "investigations",
        label: "Investigations",
        route: "/investigations",
        icon: ShieldAlert,
    },
    {
        section: "Detect & Analyze",
        id: "assets",
        label: "Assets",
        route: "/assets",
        icon: Building2,
    },
    {
        section: "Detect & Analyze",
        id: "threat-intelligence",
        label: "Threat Intelligence",
        route: "/threat-intelligence",
        icon: Shield,
    },
    {
        section: "Detect & Analyze",
        id: "exposure",
        label: "Exposure Management",
        route: "/exposure",
        icon: BarChart3,
    },
    {
        section: "Decision & Response",
        id: "decision-center",
        label: "Decision Center",
        route: "/decision-center",
        icon: Workflow,
    },
];