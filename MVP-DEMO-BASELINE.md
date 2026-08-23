# PredatorAI MVP 1.0 Demo Baseline

Status: TASK-0095 / REVIEW

This document freezes the reproducible local baseline for the existing MVP
slice. It does not add product behavior, create data, or provide enterprise
IAM.

## Canonical demo slice

```text
Greenbone Finding
  → GET /api/findings
  → SOC Dashboard / Findings
  → POST /api/findings/{finding_id}/explanation
  → configured MVP authorization
  → FindingTrustedRetrievalService
  → BoundAIContext
  → AIContextAdmissionPolicy
  → model egress allowlist
  → OpenAI explanation call
  → output disclosure policy and security guard
  → FindingExplanationResult
  → persisted Finding→Incident relationship
  → Incident Command Center
```

Verified identities:

- Finding: `6d3167e9-002c-4b76-a5a7-ce47f81b78b1`
- Finding title: `DistCC RCE Vulnerability (CVE-2004-2687)`
- Finding source: `greenbone`
- Asset: `asset-lab-metasploitable2-001`
- Threat intelligence: `CVE-2004-2687`
- Incident: `incident-task0077-distcc-live`
- Relationship: `rel-finding` / `investigation_candidate`
- Incident lifecycle: `investigating`

The Finding and Incident identities were verified from the existing
`C:\Users\sinii\Desktop\xxx.xml` report and
`runtime/incident-contexts.json`. The asset identity is present in the
existing `C:\Users\sinii\Desktop\DVWA\predatorai-dvwa-asset-context.json`.

## Environment baseline

| Variable | Requirement | Purpose / safe form |
|---|---|---|
| `GREENBONE_REPORT_PATH` | REQUIRED | Existing Greenbone XML, e.g. `C:\Users\sinii\Desktop\xxx.xml` |
| `ASSET_CONTEXT_PATH` | REQUIRED for resolved asset context | Existing asset JSON, e.g. `C:\Users\sinii\Desktop\DVWA\predatorai-dvwa-asset-context.json` |
| `INCIDENT_CONTEXT_PATH` | REQUIRED | `runtime/incident-contexts.json`; missing configuration fails closed for Incident Context |
| `AI_FINDING_EXPLANATION_ALLOWED_IDS` | REQUIRED | Exact comma-separated Finding IDs; baseline contains `6d3167e9-002c-4b76-a5a7-ce47f81b78b1`; no wildcard or allow-all |
| `OPENAI_API_KEY` | REQUIRED for live Explanation | Set only in the user environment: `OPENAI_API_KEY=<set-in-user-environment>`; value is never printed or documented |
| `VITE_API_BASE_URL` | REQUIRED for frontend/API separation | `http://127.0.0.1:8000` in the frontend process environment |

The `AI_FINDING_EXPLANATION_ALLOWED_IDS` setting is a controlled MVP demo
authorization boundary, not Enterprise IAM. Missing or non-matching IDs remain
fail-closed.

The local ignored `.env` contains the non-secret report, asset, incident and
single Finding authorization settings. The provider key is not written to this
document or to repository files.

## Reproducible startup and walkthrough

From the repository root, with the environment above loaded:

1. Start the existing FastAPI application:

   ```powershell
   $env:PYTHONPATH='.'
   python -m uvicorn api_app:app --host 127.0.0.1 --port 8000
   ```

2. In a second terminal, start the existing frontend with its API base URL:

   ```powershell
   cd frontend
   $env:VITE_API_BASE_URL='http://127.0.0.1:8000'
   npm run dev
   ```

3. Verify `GET http://127.0.0.1:8000/` and `GET /api/findings`.
4. Confirm the canonical Finding ID is present in the Findings response.
5. Open the SOC Dashboard, select the canonical Finding and request its
   Finding Explanation.
6. Confirm the existing protected explanation path completes only after the
   configured authorization, trusted retrieval, bound context, admission,
   model-egress and output-security stages.
7. Confirm the Dashboard Investigation Context shows the persisted
   `investigation_candidate` relationship.
8. Select `Open Command Center` and verify the existing route:
   `/incident-response/incidents/incident-task0077-distcc-live/command-center`.

No pre-flight step performs a provider call or mutates runtime persistence.

## Pre-flight checklist

- [x] Greenbone report exists and contains 69 findings, including the
  canonical DistCC Finding.
- [x] Asset context file exists and contains `asset-lab-metasploitable2-001`.
- [x] Incident persistence exists and contains the canonical Incident.
- [x] Finding→Incident relationship resolves to `rel-finding` with role
  `investigation_candidate`.
- [x] `AI_FINDING_EXPLANATION_ALLOWED_IDS` explicitly contains the canonical
  Finding ID.
- [x] `OPENAI_API_KEY` presence is checked without printing its value.
- [x] Backend imports successfully and exposes the FastAPI app.
- [x] No provider call is required for this pre-flight verification.

## MVP 1.0 included

- Greenbone Finding ingestion/read
- SOC Findings and Dashboard
- secure AI Finding Explanation
- Finding→Incident relationship
- Incident Command Center

## MVP 1.0 not included

- RAG, Vector DB, Agents, Tools and Multi-Agent flows
- additional providers and Provider Governance
- Enterprise IAM
- complete DLP engine
- automatic Remediation and HITL
- productive Investigation detail chain
- additional Personas and Workspaces

Updated: 2026-08-19
