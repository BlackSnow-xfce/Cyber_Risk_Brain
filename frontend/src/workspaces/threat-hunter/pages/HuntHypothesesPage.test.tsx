import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import type { HuntHypothesis } from "../HuntHypothesis";
import {
    activateHuntHypothesis,
    createHuntHypothesis,
    getHuntHypotheses,
    getHuntHypothesisReferenceResolution,
    getLocalOperatorSession,
} from "../HuntHypothesisApiClient";
import HuntHypothesesPage from "./HuntHypothesesPage";

vi.mock("../HuntHypothesisApiClient", () => ({
    activateHuntHypothesis: vi.fn(),
    getHuntHypotheses: vi.fn(),
    getHuntHypothesisReferenceResolution: vi.fn(),
    getLocalOperatorSession: vi.fn(),
    createHuntHypothesis: vi.fn(),
    LOCAL_OPERATOR_BOOTSTRAP_URL: "http://127.0.0.1:8000/api/operator/session/bootstrap",
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
        vi.clearAllMocks();
        vi.mocked(getHuntHypotheses).mockResolvedValue([]);
        vi.mocked(getLocalOperatorSession).mockResolvedValue(null);
        vi.mocked(createHuntHypothesis).mockResolvedValue({
            ...hypothesis,
            status: "draft",
        });
        vi.mocked(activateHuntHypothesis).mockResolvedValue(hypothesis);
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

    it("directs unauthenticated operators to the backend-owned bootstrap", async () => {
        render(<HuntHypothesesPage />);

        const link = await screen.findByRole("link", { name: "Authenticate Local Operator" });
        expect(link).toHaveAttribute(
            "href",
            "http://127.0.0.1:8000/api/operator/session/bootstrap",
        );
        expect(screen.queryByRole("button", { name: "Create hypothesis" })).not.toBeInTheDocument();
    });

    it("creates only human-authored fields with the session CSRF token and refreshes", async () => {
        const created = { ...hypothesis, status: "draft", hypothesis_id: "hypothesis-created" };
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:create"],
            expires_at: "2026-08-24T15:30:00Z",
            csrf_token: "csrf-token",
        });
        vi.mocked(getHuntHypotheses)
            .mockResolvedValueOnce([])
            .mockResolvedValueOnce([created]);
        vi.mocked(createHuntHypothesis).mockResolvedValueOnce(created);
        render(<HuntHypothesesPage />);

        fireEvent.click(await screen.findByRole("button", { name: "Create hypothesis" }));
        fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Manual hypothesis" } });
        fireEvent.change(screen.getByLabelText("Statement"), { target: { value: "Investigate an assumption." } });
        fireEvent.change(screen.getByLabelText("Rationale"), { target: { value: "Human review is warranted." } });
        fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

        await waitFor(() => expect(createHuntHypothesis).toHaveBeenCalledWith(
            {
                title: "Manual hypothesis",
                statement: "Investigate an assumption.",
                rationale: "Human review is warranted.",
                target_references: [],
                threat_references: [],
            },
            "csrf-token",
        ));
        expect(await screen.findByText("hypothesis-created")).toBeInTheDocument();
        expect(screen.getByText("draft")).toBeInTheDocument();
    }, 10_000);

    it("keeps the unconfirmed-assumption warning visible", async () => {
        render(<HuntHypothesesPage />);
        expect(await screen.findByText(/does not constitute evidence or confirmed compromise/i)).toBeInTheDocument();
    });

    it("activates only an authorized draft and refreshes persisted state", async () => {
        const draft = { ...hypothesis, status: "draft" };
        const active = { ...hypothesis, status: "active" };
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:activate"],
            expires_at: "2026-08-26T09:30:00Z",
            csrf_token: "csrf-token",
        });
        vi.mocked(getHuntHypotheses)
            .mockResolvedValueOnce([draft])
            .mockResolvedValueOnce([active]);
        vi.mocked(activateHuntHypothesis).mockResolvedValueOnce(active);
        render(<HuntHypothesesPage />);

        fireEvent.click(await screen.findByRole("button", {
            name: "Activate for investigation",
        }));

        await waitFor(() => expect(activateHuntHypothesis).toHaveBeenCalledWith(
            hypothesis.hypothesis_id,
            "csrf-token",
        ));
        expect(await screen.findByText("active")).toBeInTheDocument();
        expect(screen.queryByRole("button", {
            name: "Activate for investigation",
        })).not.toBeInTheDocument();
        expect(screen.getByText(/released for investigation only/i)).toBeInTheDocument();
        expect(screen.getByText(/not evidence or confirmation/i)).toBeInTheDocument();
    });

    it("does not expose activation to creation-only or non-draft sessions", async () => {
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:create"],
            expires_at: "2026-08-26T09:30:00Z",
            csrf_token: "csrf-token",
        });
        vi.mocked(getHuntHypotheses).mockResolvedValueOnce([hypothesis]);
        render(<HuntHypothesesPage />);

        await screen.findByText(hypothesis.title);
        expect(screen.queryByRole("button", {
            name: "Activate for investigation",
        })).not.toBeInTheDocument();
        expect(activateHuntHypothesis).not.toHaveBeenCalled();
    });

    it("preserves canonical activation when collection refresh fails", async () => {
        const draft = { ...hypothesis, status: "draft" };
        const active = { ...hypothesis, status: "active" };
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:activate"],
            expires_at: "2026-08-26T09:30:00Z",
            csrf_token: "csrf-token",
        });
        vi.mocked(getHuntHypotheses)
            .mockResolvedValueOnce([draft])
            .mockRejectedValueOnce(new Error("refresh unavailable"));
        vi.mocked(activateHuntHypothesis).mockResolvedValueOnce(active);
        render(<HuntHypothesesPage />);

        fireEvent.click(await screen.findByRole("button", {
            name: "Activate for investigation",
        }));

        expect(await screen.findByText("active")).toBeInTheDocument();
        expect(screen.getByText(
            "The hypothesis was activated, but the collection could not be refreshed.",
        )).toBeInTheDocument();
        expect(screen.queryByText(
            "The hypothesis could not be activated.",
        )).not.toBeInTheDocument();
        expect(screen.queryByRole("button", {
            name: "Activate for investigation",
        })).not.toBeInTheDocument();
    });

    it("rejects duplicate pointers before submission", async () => {
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:create"],
            expires_at: "2026-08-24T15:30:00Z",
            csrf_token: "csrf-token",
        });
        render(<HuntHypothesesPage />);
        fireEvent.click(await screen.findByRole("button", { name: "Create hypothesis" }));
        const referenceIds = screen.getAllByLabelText("Reference ID");
        const addButtons = screen.getAllByRole("button", { name: "Add" });
        fireEvent.change(referenceIds[0], { target: { value: "asset-001" } });
        fireEvent.click(addButtons[0]);
        fireEvent.change(referenceIds[0], { target: { value: "asset-001" } });
        fireEvent.click(addButtons[0]);
        expect(screen.getByText("Duplicate reference pointers are not allowed.")).toBeInTheDocument();
    });

    it("reports creation failure without fabricating a new hypothesis", async () => {
        vi.mocked(getLocalOperatorSession).mockResolvedValueOnce({
            principal_id: "product-owner",
            display_name: "Product Owner",
            principal_type: "human/operator",
            granted_permissions: ["hunt_hypothesis:create"],
            expires_at: "2026-08-24T15:30:00Z",
            csrf_token: "csrf-token",
        });
        vi.mocked(createHuntHypothesis).mockRejectedValueOnce(new Error("denied"));
        render(<HuntHypothesesPage />);
        fireEvent.click(await screen.findByRole("button", { name: "Create hypothesis" }));
        fireEvent.change(screen.getByLabelText("Title"), { target: { value: "Manual hypothesis" } });
        fireEvent.change(screen.getByLabelText("Statement"), { target: { value: "Investigate an assumption." } });
        fireEvent.change(screen.getByLabelText("Rationale"), { target: { value: "Human review is warranted." } });
        fireEvent.click(screen.getByRole("button", { name: "Create draft" }));

        expect(await screen.findByText("The hypothesis could not be created.")).toBeInTheDocument();
        expect(screen.getByRole("dialog")).toBeInTheDocument();
        expect(screen.queryByText("hypothesis-created")).not.toBeInTheDocument();
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
        expect(screen.queryByText(/hypothesis confirms compromise/i)).not.toBeInTheDocument();
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
        expect(screen.queryByText(/hypothesis confirms compromise/i)).not.toBeInTheDocument();
    });
});
