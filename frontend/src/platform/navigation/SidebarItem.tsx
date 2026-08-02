import { ChevronRight } from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

interface SidebarItemProps {
    item: NavigationItem;
    active?: boolean;
}

export default function SidebarItem({
    item,
    active = false,
}: SidebarItemProps) {
    const Icon = item.icon;

    return (
        <button
            className={
                active
                    ? "sidebar-item sidebar-item-active"
                    : "sidebar-item"
            }
        >
            <Icon size={18} />

            <span>{item.label}</span>

            {item.children && (
                <ChevronRight size={16} />
            )}
        </button>
    );
}