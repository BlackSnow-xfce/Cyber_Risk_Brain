import {
    BarChart3,
    Briefcase,
    Building2,
    Shield,
    ShieldAlert,
    TrendingUp,
} from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

export const executiveNavigation: NavigationItem[] = [
    {
        section: "Executive",

        id: "overview",

        label: "Executive Overview",

        route: "/",

        icon: Briefcase,
    },

    {
        section: "Executive",

        id: "enterprise-risk",

        label: "Enterprise Risk",

        route: "/risk",

        icon: ShieldAlert,
    },

    {
        section: "Executive",

        id: "business-impact",

        label: "Business Impact",

        route: "/business-impact",

        icon: Building2,
    },

    {
        section: "Executive",

        id: "compliance",

        label: "Compliance",

        route: "/compliance",

        icon: Shield,
    },

    {
        section: "Executive",

        id: "reports",

        label: "Reports",

        route: "/reports",

        icon: BarChart3,
    },

    {
        section: "Executive",

        id: "trends",

        label: "Strategic Trends",

        route: "/trends",

        icon: TrendingUp,
    },
];