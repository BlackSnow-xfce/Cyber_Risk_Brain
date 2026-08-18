import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, describe, expect, it } from "vitest";

import DashboardPage from "./DashboardPage";

const findings = [
    {
        id: "finding-1",
        source: "greenbone",
        title: "DistCC RCE Vulnerability",
        vendorSeverity: "High",
        asset: "asset-lab-metasploitable2-001",
    },
];

function LocationProbe() {
    const { pathname } = useLocation();
    return <output data-testid="location">{pathname}</output>;
}

describe("SOC Analyst dashboard foundation", () => {
    afterEach(() => {
        cleanup();
    });

    it("renders the operational SOC structure without mock decision data", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve(findings)} />
            </MemoryRouter>,
        );

        expect(screen.getByText("SOC Analyst")).toBeInTheDocument();
        expect(screen.getByLabelText("Operational status")).toBeInTheDocument();
        expect(screen.getByLabelText("Analyst workspace")).toBeInTheDocument();
        expect(screen.getByText("Context & Insights")).toBeInTheDocument();
        expect(screen.queryByText("Decision Workspace")).not.toBeInTheDocument();
        expect(await screen.findByText("DistCC RCE Vulnerability")).toBeInTheDocument();
        expect(screen.getByText("1", { selector: "h4" })).toBeInTheDocument();
    });

    it("keeps the real findings navigation entry point", () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve(findings)} />
                <LocationProbe />
            </MemoryRouter>,
        );

        fireEvent.click(screen.getByRole("button", { name: "Open Findings" }));

        expect(screen.getByTestId("location")).toHaveTextContent("/findings");
    });

    it("shows a neutral empty state", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.resolve([])} />
            </MemoryRouter>,
        );

        expect(await screen.findByText("No live findings available.")).toBeInTheDocument();
        expect(screen.getAllByText("—").length).toBeGreaterThan(0);
    });

    it("shows a controlled error state", async () => {
        render(
            <MemoryRouter initialEntries={["/"]}>
                <DashboardPage loadFindings={() => Promise.reject(new Error("offline"))} />
            </MemoryRouter>,
        );

        expect(await screen.findByText("Live findings could not be loaded.")).toBeInTheDocument();
        expect(screen.getByText("Unavailable")).toBeInTheDocument();
    });
});
