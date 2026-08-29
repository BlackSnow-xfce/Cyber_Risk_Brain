import { readFileSync } from "node:fs";

import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { Shield } from "lucide-react";
import { MemoryRouter, useLocation, useNavigate } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import { WorkspaceProvider } from "@/context/WorkspaceContext";
import { WorkspaceId } from "@/types/workspace";
import type { NavigationItem } from "@/workspaces/navigation";
import { getWorkspaceNavigation, workspaceRegistry } from "@/workspaces";

import Sidebar from "./Sidebar";
import SidebarItem from "./SidebarItem";

const sidebarSelectorPattern = /(?:^|})\s*\.sidebar(?:[-\w]|\s|>|:|\.)*\s*\{/;
const canonicalRules: ReadonlyArray<readonly [string, ReadonlyArray<string>]> = [
    [".sidebar", ["width: 164px", "min-width: 164px", "height: 100vh", "overflow: hidden"]],
    [".sidebar-logo", ["display: flex", "align-items: center", "gap: 7px", "height: 52px", "padding: 7px 10px"]],
    [".sidebar-section", ["padding: 6px 6px 0"]],
    [".sidebar-title", ["font-size: 13px", "font-weight: 600", "margin: 0 5px 3px"]],
    [".sidebar-item", ["width: 100%", "min-height: 28px", "display: flex", "align-items: center", "gap: 7px", "padding: 0 8px", "border-radius: 4px"]],
    [".sidebar-item span", ["font-size: 14px", "flex: 1 1 auto", "min-width: 0", "white-space: nowrap", "overflow: hidden", "text-overflow: ellipsis"]],
    [".sidebar-item svg", ["flex: 0 0 auto"]],
    [".sidebar-item:hover", ["background: #101a30", "color: white"]],
    [".sidebar-item-active", ["background: linear-gradient(", "color: white"]],
];

const canonicalNavigationLabels = new Map<WorkspaceId, readonly string[]>([
    [WorkspaceId.DECISION_CENTER, ["Exposure Management", "Threat Intelligence", "Executive Summary"]],
    [WorkspaceId.EXECUTIVE, ["Critical Business Services", "Investment Priorities", "Executive Dashboard", "Strategic Decisions"]],
    [WorkspaceId.THREAT_HUNTING, ["Query Workspace", "Hunt Timeline"]],
    [WorkspaceId.THREAT_INTELLIGENCE, ["Our Environment"]],
    [WorkspaceId.INCIDENT_RESPONSE, ["Active Incidents", "Response Actions"]],
    [WorkspaceId.RISK_MANAGEMENT, ["Business Services", "Executive Reports"]],
    [WorkspaceId.ADMINISTRATION, ["Background Jobs", "Platform Health", "Synchronization", "System Overview", "System Settings"]],
]);

const sidebarWidth = 164;
const sectionHorizontalPadding = 6 * 2;
const itemHorizontalPadding = 8 * 2;
const leadingIconWidth = 12;
const trailingChevronWidth = 11;
const itemGap = 7;

function calculateTextBudget(hasChevron: boolean): number {
    const iconWidths = leadingIconWidth
        + (hasChevron ? trailingChevronWidth : 0);
    const gaps = itemGap * (hasChevron ? 2 : 1);

    return sidebarWidth
        - sectionHorizontalPadding
        - itemHorizontalPadding
        - iconWidths
        - gaps;
}

function satisfiesSidebarCascadeContract(
    sidebarSource: string,
    globalSource: string,
): boolean {
    const normalizedSource = sidebarSource.replace(/\s+/g, " ");

    return !sidebarSelectorPattern.test(globalSource)
        && canonicalRules.every(([selector, declarations]) => {
            const escapedSelector = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
            const rule = normalizedSource.match(new RegExp(`${escapedSelector}\\s*\\{([^}]*)\\}`))?.[1];
            return rule !== undefined
                && declarations.every((declaration) => rule.includes(declaration));
        });
}

function LocationProbe() {
    const { pathname, search } = useLocation();
    return <output data-testid="location">{pathname}{search}</output>;
}

function BackProbe() {
    const navigate = useNavigate();
    return (
        <button onClick={() => navigate(-1)}>
            Back
        </button>
    );
}

function renderSidebar(initialEntries: string[]) {
    return render(
        <WorkspaceProvider>
            <MemoryRouter initialEntries={initialEntries}>
                <Sidebar />
                <LocationProbe />
            </MemoryRouter>
        </WorkspaceProvider>,
    );
}

function renderSidebarWithBack(initialEntries: string[], initialIndex: number) {
    return render(
        <WorkspaceProvider>
            <MemoryRouter
                initialEntries={initialEntries}
                initialIndex={initialIndex}
            >
                <Sidebar />
                <LocationProbe />
                <BackProbe />
            </MemoryRouter>
        </WorkspaceProvider>,
    );
}

describe("Sidebar routing", () => {
    afterEach(() => {
        cleanup();
    });

    it("makes Sidebar.css the sole authority for the complete production cascade", () => {
        const sidebarSource = readFileSync("src/platform/navigation/Sidebar.css", "utf8");
        const globalSource = readFileSync("src/styles/global.css", "utf8");

        expect(satisfiesSidebarCascadeContract(sidebarSource, globalSource)).toBe(true);
        expect(globalSource).not.toMatch(sidebarSelectorPattern);
        expect(globalSource).toContain("--text-secondary:");
        expect(globalSource).toContain("--surface-hover:");
        expect(globalSource).toContain("--accent:");
        expect(globalSource).toMatch(/\.platform-layout\s*\{/);
        expect(globalSource).toMatch(/\.platform-content\s*\{/);

        const legacyConflicts = [
            ".sidebar { width: 270px; min-width: 270px; overflow: auto; }",
            ".sidebar-logo { gap: 14px; padding: 24px; }",
            ".sidebar-section { padding: 22px 14px 0; }",
            ".sidebar-title { margin: 0 0 10px; font-size: 11px; font-weight: 700; }",
            ".sidebar-item { min-height: 52px; gap: 14px; padding: 12px 14px; border-radius: 10px; overflow: hidden; }",
            ".sidebar-item:hover { background: var(--surface-hover); }",
            ".sidebar-item-active { background: var(--accent); }",
        ];

        for (const conflict of legacyConflicts) {
            expect(satisfiesSidebarCascadeContract(
                sidebarSource,
                `${globalSource}\n${conflict}`,
            )).toBe(false);
        }
    });

    it("uses the readable Sidebar typography contract", () => {
        const sidebarSource = readFileSync("src/platform/navigation/Sidebar.css", "utf8");

        expect(sidebarSource).toMatch(
            /\.sidebar-item span\s*\{[^}]*\bfont-size:\s*14px\s*;/s,
        );
        expect(sidebarSource).toMatch(
            /\.sidebar-title\s*\{[^}]*\bfont-size:\s*13px\s*;[^}]*\bfont-weight:\s*600\s*;/s,
        );
        expect(sidebarSource).toMatch(
            /\.sidebar\s*\{[^}]*\bwidth:\s*164px\s*;[^}]*\bmin-width:\s*164px\s*;/s,
        );
    });

    it("keeps long canonical labels inside compact, flex-stable items", () => {
        const sidebarSource = readFileSync("src/platform/navigation/Sidebar.css", "utf8");
        const itemRule = sidebarSource.match(/\.sidebar-item\s*\{([^}]*)\}/s)?.[1] ?? "";
        const labelRule = sidebarSource.match(/\.sidebar-item span\s*\{([^}]*)\}/s)?.[1] ?? "";
        const iconRule = sidebarSource.match(/\.sidebar-item svg\s*\{([^}]*)\}/s)?.[1] ?? "";

        expect(itemRule).toMatch(/\bmin-height:\s*28px\s*;/);
        expect(itemRule).not.toMatch(/(?:^|;)\s*height\s*:\s*24px\s*;/);
        expect(itemRule).toMatch(/\bdisplay:\s*flex\s*;/);
        expect(itemRule).toMatch(/\balign-items:\s*center\s*;/);
        expect(iconRule).toMatch(/\bflex:\s*0 0 auto\s*;/);
        expect(labelRule).toMatch(/\bflex:\s*1 1 auto\s*;/);
        expect(labelRule).toMatch(/\bmin-width:\s*0\s*;/);
        expect(labelRule).toMatch(/\bwhite-space:\s*nowrap\s*;/);
        expect(labelRule).toMatch(/\boverflow:\s*hidden\s*;/);
        expect(labelRule).toMatch(/\btext-overflow:\s*ellipsis\s*;/);

        expect(calculateTextBudget(false)).toBe(117);
        expect(calculateTextBudget(true)).toBe(99);
        expect(calculateTextBudget(false)).toBeGreaterThan(0);
        expect(calculateTextBudget(true)).toBeGreaterThan(0);

        expect(sidebarSource).not.toMatch(
            /\.sidebar-item(?:\s|:[^{]+)*\{[^}]*(?:overflow|text-overflow)\s*:/s,
        );
    });

    it("uses all canonical workspace navigation sources for the real labels", () => {
        for (const [workspace, expectedLabels] of canonicalNavigationLabels) {
            const labels = getWorkspaceNavigation(workspace).map((item) => item.label);

            for (const expectedLabel of expectedLabels) {
                expect(labels).toContain(expectedLabel);
            }
        }

        const allNavigationLabels = [...canonicalNavigationLabels.keys()]
            .flatMap((workspace) => getWorkspaceNavigation(workspace))
            .map((item) => item.label);
        const incidentResponseWorkspace = workspaceRegistry.find(
            (workspace) => workspace.id === WorkspaceId.INCIDENT_RESPONSE,
        );

        expect(incidentResponseWorkspace?.name).toBe("Incident Response");
        expect(allNavigationLabels).not.toContain("Incident Response");
    });

    it("renders the actual SidebarItem icon, ellipsis label, Chevron and selected state", () => {
        const item: NavigationItem = {
            id: "controlled-parent",
            label: "Controlled canonical navigation label",
            section: "Controlled",
            route: "/controlled",
            icon: Shield,
            children: [],
        };
        const { container } = render(<SidebarItem item={item} active />);
        const button = screen.getByRole("button", { name: item.label });
        const label = button.querySelector("span");
        const icons = button.querySelectorAll("svg");

        expect(button).toHaveClass("sidebar-item", "sidebar-item-active");
        expect(label).toHaveTextContent(item.label);
        expect(icons).toHaveLength(2);
        expect(icons[0]).toHaveAttribute("width", "12");
        expect(icons[1]).toHaveAttribute("width", "11");
        expect(container.querySelector(".sidebar-item > span")).toBe(label);
    });

    it("navigates from the command center to Dashboard", () => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        fireEvent.click(screen.getByRole("button", { name: "Dashboard" }));

        expect(screen.getByTestId("location")).toHaveTextContent("/");
        expect(screen.getByRole("button", { name: "Dashboard" })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("preserves the validated Finding context when navigating to Dashboard", () => {
        renderSidebar(["/findings?findingId=finding-real-001"]);

        fireEvent.click(screen.getByRole("button", { name: "Dashboard" }));

        expect(screen.getByTestId("location")).toHaveTextContent(
            "/?findingId=finding-real-001",
        );
    });

    it.each([
        ["Findings", "/findings"],
        ["Investigations", "/investigations"],
    ])("navigates to %s", (label, route) => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        fireEvent.click(screen.getByRole("button", { name: label }));

        expect(screen.getByTestId("location")).toHaveTextContent(route);
        expect(screen.getByRole("button", { name: label })).toHaveClass(
            "sidebar-item-active",
        );
    });

    it("does not mark Dashboard active on the command center path", () => {
        renderSidebar([
            "/incident-response/incidents/incident-real-001/command-center",
        ]);

        expect(screen.getByRole("button", { name: "Dashboard" })).not.toHaveClass(
            "sidebar-item-active",
        );
    });

    it("restores the command center path with browser back", () => {
        renderSidebarWithBack(
            [
                "/incident-response/incidents/incident-real-001/command-center",
                "/findings",
            ],
            1,
        );

        fireEvent.click(screen.getByRole("button", { name: "Back" }));

        expect(screen.getByTestId("location")).toHaveTextContent(
            "/incident-response/incidents/incident-real-001/command-center",
        );
        expect(screen.getByRole("button", { name: "Dashboard" })).not.toHaveClass(
            "sidebar-item-active",
        );
    });
});
