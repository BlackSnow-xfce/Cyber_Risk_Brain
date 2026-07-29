import {
    BarChart3,
    Briefcase,
    Building2,
    Gauge,
    LayoutDashboard,
    Search,
    Shield,
    ShieldAlert,
    Target,
    Workflow,
    ChevronRight,
    ChevronsLeft,
} from "lucide-react";

import "./Sidebar.css";

export function Sidebar() {
    return (
        <aside className="sidebar">

            <div className="sidebar-logo">

                <img
                    src="/logo.png"
                    alt="PredatorAI"
                    className="sidebar-logo-image"
                />

                <div className="sidebar-logo-text">

                    <div>PredatorAI</div>

                    <small>v3</small>

                </div>

            </div>

            <div className="sidebar-section">

                <span className="sidebar-title">
                    OVERVIEW
                </span>

                <button className="sidebar-item sidebar-item-active">
                    <LayoutDashboard size={18} />
                    <span>Dashboard</span>
                    <ChevronRight size={16} />
                </button>

                <button className="sidebar-item">
                    <Briefcase size={18} />
                    <span>Executive Summary</span>
                </button>

                <button className="sidebar-item">
                    <Gauge size={18} />
                    <span>Risk Posture</span>
                </button>

                <button className="sidebar-item">
                    <Target size={18} />
                    <span>Attack Surface</span>
                </button>

            </div>

            <div className="sidebar-section">

                <span className="sidebar-title">
                    DETECT & ANALYZE
                </span>

                <button className="sidebar-item">
                    <Search size={18} />
                    <span>Findings</span>
                    <ChevronRight size={16} />
                </button>

                <button className="sidebar-item">
                    <ShieldAlert size={18} />
                    <span>Investigations</span>
                </button>

                <button className="sidebar-item">
                    <Building2 size={18} />
                    <span>Assets</span>
                </button>

                <button className="sidebar-item">
                    <Shield size={18} />
                    <span>Threat Intelligence</span>
                </button>

                <button className="sidebar-item">
                    <BarChart3 size={18} />
                    <span>Exposure Management</span>
                </button>

            </div>

            <div className="sidebar-section">

                <span className="sidebar-title">
                    DECISION & RESPONSE
                </span>

                <button className="sidebar-item">
                    <Workflow size={18} />
                    <span>Decision Center</span>
                    <ChevronRight size={16} />
                </button>

            </div>

            <div className="sidebar-spacer" />

            <button className="sidebar-collapse">
                <ChevronsLeft size={18} />
                Collapse
            </button>

        </aside>
    );
}