import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { HuntHypothesis } from "../HuntHypothesis";
import { getHuntHypotheses } from "../HuntHypothesisApiClient";
import ThreatHunterOverviewPage from "./ThreatHunterOverviewPage";

vi.mock("../HuntHypothesisApiClient", () => ({ getHuntHypotheses: vi.fn() }));

const hypothesis: HuntHypothesis = {
    hypothesis_id: "hypothesis-001",
    title: "Review administrative execution",
    statement: "An operator-authored assumption.",
    status: "draft",
    created_at: "2026-08-29T10:00:00Z",
    created_by: "operator-001",
    target_references: [],
    threat_references: [],
    rationale: "Investigation is warranted.",
    contract_version: "1.0",
};

function renderPage() {
    return render(
        <MemoryRouter>
            <ThreatHunterOverviewPage />
        </MemoryRouter>,
    );
}

describe("ThreatHunterOverviewPage", () => {
    afterEach(() => cleanup());

    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(getHuntHypotheses).mockResolvedValue([]);
    });

    it("renders the reference hierarchy with two operational cards", async () => {
        renderPage();

        expect(screen.getByText("Proactive discovery workspace")).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "Threat Hunter Mission Console" })).toBeInTheDocument();
        expect(screen.getByRole("heading", { name: "Hunt work area" })).toBeInTheDocument();
        expect(screen.getAllByRole("article")).toHaveLength(2);
        expect(screen.queryByText("Query Workspace")).not.toBeInTheDocument();
        expect(await screen.findByText("No data")).toBeInTheDocument();
    });

    it("keeps active hunts explicitly unavailable and uses canonical actions", async () => {
        renderPage();

        expect(screen.getByText("Not connected")).toBeInTheDocument();
        expect(screen.getByText(/No active hunts are available/)).toBeInTheDocument();
        expect(screen.getByRole("link", { name: "View hunts" })).toHaveAttribute("href", "/threat-hunting/hunts");
        expect(screen.getByRole("link", { name: "Open hypotheses" })).toHaveAttribute("href", "/threat-hunting/hypotheses");
        expect(await screen.findByText("No persisted hunt hypotheses are available.")).toBeInTheDocument();
    });

    it("shows loading without a count while the repository request is pending", () => {
        vi.mocked(getHuntHypotheses).mockReturnValueOnce(new Promise(() => undefined));
        renderPage();
        expect(screen.getByRole("status")).toHaveTextContent("Loading persisted hypotheses");
        expect(screen.queryByText("No data")).not.toBeInTheDocument();
    });

    it("distinguishes repository failure from an empty collection", async () => {
        vi.mocked(getHuntHypotheses).mockRejectedValueOnce(new Error("unavailable"));
        renderPage();
        expect(await screen.findByRole("alert")).toHaveTextContent("Repository unavailable");
        expect(screen.queryByText("No data")).not.toBeInTheDocument();
        expect(screen.queryByText(/No persisted/)).not.toBeInTheDocument();
    });

    it("shows only the authoritative persisted hypothesis count", async () => {
        vi.mocked(getHuntHypotheses).mockResolvedValueOnce([
            hypothesis,
            { ...hypothesis, hypothesis_id: "hypothesis-002" },
        ]);
        renderPage();
        expect(await screen.findByText("2")).toBeInTheDocument();
        expect(screen.getByText("Persisted hunt hypotheses")).toBeInTheDocument();
        expect(screen.queryByText("No data")).not.toBeInTheDocument();
    });
});
