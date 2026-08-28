import { ChevronRight } from "lucide-react";

import type { NavigationItem } from "@/workspaces/navigation";

interface SidebarItemProps {
    item: NavigationItem;
    active?: boolean;
    onSelect?: (itemId: string) => void;
}

export default function SidebarItem({
    item,
    active = false,
    onSelect,
}: SidebarItemProps) {
    const Icon = item.icon;

    return (
        <button
            type="button"
            onClick={() => onSelect?.(item.id)}
            disabled={item.enabled === false}
            className={
                active
                    ? "sidebar-item sidebar-item-active"
                    : "sidebar-item"
            }
        >
            <Icon size={12} />

            <span>{item.label}</span>

            {item.children && (
                <ChevronRight size={11} />
            )}
        </button>
    );
}
