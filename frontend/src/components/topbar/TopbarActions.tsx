import { useState } from "react";
import { Bell, CalendarDays, HelpCircle, RefreshCw, Search, Sparkles, Sun } from "lucide-react";
import { useNavigate } from "react-router-dom";

export default function TopbarActions() {
    const navigate = useNavigate();
    const [themeOpen, setThemeOpen] = useState(false);
    return <div className="topbar-actions">
        <button className="topbar-control topbar-icon-control" type="button" disabled aria-label="Calendar unavailable"><CalendarDays size={11} /></button>
        <button className="topbar-control topbar-icon-control" type="button" disabled aria-label="Refresh unavailable"><RefreshCw size={11} /></button>
        <button className="topbar-control topbar-explain" type="button" onClick={() => navigate("/explainability")}><Sparkles size={11} />Explain This Dashboard</button>
        <button className="topbar-control topbar-search" type="button" disabled><Search size={11} />Search unavailable</button>
        <button className="topbar-control topbar-icon-control" type="button" disabled aria-label="Notifications unavailable"><Bell size={11} /></button>
        <button className="topbar-control topbar-icon-control" type="button" disabled aria-label="Help unavailable"><HelpCircle size={11} /></button>
        <span className="theme-wrap">
            <button className="topbar-control topbar-icon-control" type="button" aria-label="Theme" aria-expanded={themeOpen} onClick={() => setThemeOpen((open) => !open)}><Sun size={11} /></button>
            {themeOpen && <section className="theme-popover" aria-label="Theme options"><h2>Theme</h2><div className="theme-options"><span className="theme-option theme-option-active">Dark (Purple)</span><span className="theme-option">Light</span><span className="theme-option">Light (Blue)</span></div></section>}
        </span>
    </div>;
}
