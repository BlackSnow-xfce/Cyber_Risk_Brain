import type { NavigationItem } from "@/workspaces/navigation";

import SidebarItem from "./SidebarItem";

interface SidebarSectionProps {
    title: string;
    items: NavigationItem[];
}

export default function SidebarSection({
    title,
    items,
}: SidebarSectionProps) {
    return (
        <div className="sidebar-section">
            <span className="sidebar-title">
                {title}
            </span>

            {items.map((item) => (
                <SidebarItem
                    key={item.id}
                    item={item}
                    active={item.id === "dashboard"}
                />
            ))}
        </div>
    );
}