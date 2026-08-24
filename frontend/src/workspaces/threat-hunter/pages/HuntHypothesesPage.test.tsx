import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { HuntHypothesis } from "../HuntHypothesis";
import { getHuntHypotheses } from "../HuntHypothesisApiClient";
import HuntHypothesesPage from "./HuntHypothesesPage";

vi.mock("../HuntHypothesisApiClient", () => ({
    getHuntHypotheses: vi.fn(),
    HuntHypothesisRequestError: class HuntHypothesisRequestError extends Error {
        status: number | null;
        constructor(status: number | null) {
            super();
            this.status = status;
        }
    },
}));

const hypothesis: HuntHypothesis = {
    hypothesis_id: "hypothesis-001",
    title: "Administrative execution from an exposed service",
    statement: "A service account may be executing unexpected commands.",
    status: "active",
    created_at: "2026-08-24T10:00:00Z",
    created_by: "threat-hunter-001",
    target_references: [{ reference_type: "asset", reference_id: "asset-001" }],
    threat_references: [{ reference_type: "technique", reference_id: "T1059" }],
    rationale: "Unexpected command execution warrants investigation.",
    contract_version: "1.0",
};

describe("HuntHypothesesPage", () => {
    afterEach(() => cleanup());

    beforeEach(() => {
        vi.mocked(getHuntHypotheses).mockResolvedValue([]);
    });

    it("shows loading while the repository request is pending", () => {
        vi.mocked(getHuntHypotheses).mockReturnValueOnce(new Promise(() => undefined));

        render(<HuntHypothesesPage />);

        expect(screen.getByText("Loading hunt hypotheses…")).toBeInTheDocument();
    });

    it("shows the truthful empty state", async () => {
        render(<HuntHypothesesPage />);

        expect(
            await screen.findByText("No persisted hunt hypotheses are available."),
        ).toBeInTheDocument();
    });

    it("shows repository errors without an empty-state claim", async () => {
        vi.mocked(getHuntHypotheses).mockRejectedValueOnce(new Error("invalid"));

        render(<HuntHypothesesPage />);

        expect(await screen.findByText("Hunt hypotheses could not be loaded.")).toBeInTheDocument();
        expect(screen.queryByText(/No persisted/)).not.toBeInTheDocument();
    });

    it("renders only the canonical projection and unresolved references", async () => {
        vi.mocked(getHuntHypotheses).mockResolvedValueOnce([hypothesis]);

        render(<HuntHypothesesPage />);

        expect(await screen.findByText(hypothesis.title)).toBeInTheDocument();
        expect(screen.getByText(hypothesis.statement)).toBeInTheDocument();
        expect(screen.getByText("active")).toBeInTheDocument();
        expect(screen.getByText(/threat-hunter-001/)).toBeInTheDocument();
        expect(screen.getByText("Unresolved target references")).toBeInTheDocument();
        expect(screen.getByText("asset: asset-001")).toBeInTheDocument();
        expect(screen.getByText("Unresolved threat references")).toBeInTheDocument();
        expect(screen.getByText("technique: T1059")).toBeInTheDocument();
        expect(screen.getByText(/unconfirmed assumptions/i)).toBeInTheDocument();
        expect(screen.queryByText(/confirmed compromise/i)).not.toBeInTheDocument();
    });
});
