import { WorkspaceSelector } from "@/components/topbar";

import "./Topbar.css";

export function Topbar() {
    return (
        <header className="topbar">
            <div className="topbar-left">
                <h1 className="topbar-title">
                    Dashboard
                </h1>

                <WorkspaceSelector />
            </div>

            <div className="topbar-right">
                <select className="time-select">
                    <option>Last 7 Days</option>
                </select>

                <button className="topbar-icon">
                    ⟳
                </button>

                <button className="topbar-icon">
                    ⤴
                </button>

                <button className="explain-button">
                    Explain This Dashboard
                </button>

                <button className="topbar-icon">
                    🔍
                </button>

                <button className="topbar-icon">
                    🔔
                </button>

                <button className="topbar-icon">
                    ☾
                </button>

                <div className="user-profile">
                    <div>
                        <div className="user-name">
                            Max Mustermann
                        </div>

                        <div className="user-role">
                            Security Admin
                        </div>
                    </div>

                    <div className="avatar">
                        MM
                    </div>
                </div>
            </div>
        </header>
    );
}