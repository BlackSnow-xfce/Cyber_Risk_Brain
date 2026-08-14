import {
    Binoculars,
    Bookmark,
    Boxes,
    Clock3,
    Crosshair,
    FlaskConical,
    LayoutDashboard,
    Network,
    SearchCode,
} from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

export const threatHunterNavigation: NavigationItem[] = [
    {
        section: "Hunt Operations",
        id: "overview",
        label: "Overview",
        route: "/threat-hunting",
        icon: LayoutDashboard,
    },
    {
        section: "Hunt Operations",
        id: "hunts",
        label: "Hunts",
        route: "/threat-hunting/hunts",
        icon: Binoculars,
    },
    {
        section: "Hunt Operations",
        id: "hypotheses",
        label: "Hypotheses",
        route: "/threat-hunting/hypotheses",
        icon: FlaskConical,
    },
    {
        section: "Hunt Operations",
        id: "query-workspace",
        label: "Query Workspace",
        route: "/threat-hunting/queries",
        icon: SearchCode,
    },
    {
        section: "Investigation Context",
        id: "ioc-explorer",
        label: "IOC Explorer",
        route: "/threat-hunting/iocs",
        icon: Crosshair,
    },
    {
        section: "Investigation Context",
        id: "entities",
        label: "Entities",
        route: "/threat-hunting/entities",
        icon: Boxes,
    },
    {
        section: "Investigation Context",
        id: "mitre-attack",
        label: "MITRE ATT&CK",
        route: "/threat-hunting/mitre-attack",
        icon: Network,
    },
    {
        section: "Hunt History",
        id: "hunt-timeline",
        label: "Hunt Timeline",
        route: "/threat-hunting/timeline",
        icon: Clock3,
    },
    {
        section: "Hunt History",
        id: "saved-hunts",
        label: "Saved Hunts",
        route: "/threat-hunting/saved",
        icon: Bookmark,
    },
];
