import { Menu } from "lucide-react";

import { TimeRangeSelector, TopbarActions, UserMenu, WorkspaceSwitcher } from "@/components/topbar";

import "./Topbar.css";

export default function Topbar() {
    return <header className="enterprise-topbar">
        <button className="topbar-menu" type="button" disabled aria-label="Menu unavailable"><Menu size={15} /></button>
        <div className="topbar-heading"><div><h1>Dashboard</h1><WorkspaceSwitcher /></div><span>Welcome back. Live operator identity unavailable.</span></div>
        <div className="topbar-controls"><TimeRangeSelector /><TopbarActions /><UserMenu /></div>
    </header>;
}
