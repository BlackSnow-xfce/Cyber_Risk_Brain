import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { HuntHypothesis } from "../HuntHypothesis";
import {
    getHuntHypotheses,
    getHuntHypothesisReferenceResolution,
} from "../HuntHypothesisApiClient";
import HuntHypothesesPage from "./HuntHypothesesPage";

vi.mock("../HuntHypothesisApiClient", () => ({
    getHuntHypotheses: vi.fn(),
    getHuntHypothesisReferenceResolution: vi.fn(),
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
        vi.mocked(getHuntHypothesisReferenceResolution).mockResolvedValue({
            hypothesis_id: hypothesis.hypothesis_id,
            references: [],
        });
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

    it("resolves references only on demand and preserves every canonical pointer", async () => {
        const hypothesisWithMixedReferences: HuntHypothesis = {
            ...hypothesis,
            target_references: [
                { reference_type: "asset", reference_id: "asset-001" },
                { reference_type: "finding", reference_id: "finding-missing" },
            ],
            threat_references: [
                { reference_type: "cve", reference_id: "CVE-2026-1234" },
                { reference_type: "technique", reference_id: "T1059" },
            ],
        };
        vi.mocked(getHuntHypotheses).mockResolvedValueOnce([
            hypothesisWithMixedReferences,
        ]);
        vi.mocked(getHuntHypothesisReferenceResolution).mockResolvedValueOnce({
            hypothesis_id: hypothesis.hypothesis_id,
            references: [
                {
                    reference_type: "asset",
                    reference_id: "asset-001",
                    resolution_status: "resolved",
                    authoritative_source: "asset_context",
                    resolved_identity: "asset-001",
                    source_reference: "asset-source:001",
                },
                {
                    reference_type: "finding",
                    reference_id: "finding-missing",
                    resolution_status: "not_found",
                    authoritative_source: "findings",
                    resolved_identity: null,
                    source_reference: null,
                },
                {
                    reference_type: "cve",
                    reference_id: "CVE-2026-1234",
                    resolution_status: "source_unavailable",
                    authoritative_source: "threat_intelligence",
                    resolved_identity: null,
                    source_reference: null,
                },
                {
                    reference_type: "technique",
                    reference_id: "T1059",
                    resolution_status: "unsupported",
                    authoritative_source: null,
                    resolved_identity: null,
                    source_reference: null,
                },
            ],
        });

        render(<HuntHypothesesPage />);
        await screen.findByText(hypothesis.title);

        expect(getHuntHypothesisReferenceResolution).not.toHaveBeenCalled();
        expect(screen.getByText("asset: asset-001")).toBeInTheDocument();

        fireEvent.click(screen.getByRole("button", { name: "Resolve references" }));

        expect(await screen.findByText(/Resolved identity/)).toBeInTheDocument();
        expect(screen.getByText(/Exact identity not found/)).toBeInTheDocument();
        expect(screen.getByText(/Authoritative source unavailable/)).toBeInTheDocument();
        expect(screen.getByText("Reference type unsupported")).toBeInTheDocument();
        expect(screen.getAllByText("asset: asset-001")).toHaveLength(2);
        expect(
            screen.getByText(/does not establish evidence or the truth/i),
        ).toBeInTheDocument();
        expect(getHuntHypothesisReferenceResolution).toHaveBeenCalledWith(
            hypothesis.hypothesis_id,
        );
        expect(screen.queryByText(/confirmed compromise/i)).not.toBeInTheDocument();
    });
});
