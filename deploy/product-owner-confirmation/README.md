# Product Owner confirmation boundary

This deployment hosts the existing Product Owner confirmation core behind a first-party HTTPS service.

## Required administrator provisioning

Import `keycloak-realm.template.json`. The realm binds `aidp-product-owner-browser` as its browser flow and requires both username/password and OTP executions. The client remains confidential, requires PKCE S256, the dedicated `aidp-product-owner` role, and the approved TOTP ACR.

Create a TLS certificate/key pair for the configured `public_origin`. The deployment configuration, TLS private key, DPAPI credential files, issuance credential, and audit destination must be outside every governed Git worktree and Git metadata. On Windows the service also rejects reparse-point traversal, unsafe ownership, and broad writable ACLs.

Create the Keycloak client secret as a current-user Windows DPAPI-protected JSON document:

```json
{
  "schema_version": "aidp-dpapi-secret-v2",
  "client_id": "aidp-product-owner",
  "protection_scope": "current-user",
  "principal_sid": "<service-account SID>",
  "ciphertext": "<base64 DPAPI ciphertext>"
}
```

DPAPI protection must use optional entropy equal to the ASCII SHA-256 canonical digest of `{client_id, principal_sid}`. The service rejects another Windows principal or any scope other than `current-user`.

Create a second DPAPI document with the same v2 structure using client ID `aidp-product-owner-issuer`. Its plaintext is a random value of at least 32 characters used only by the trusted local watcher/operator when calling `/product-owner/issue`.

The plaintext values must never be placed in Git, deployment JSON, command-line arguments, ordinary environment variables, logs, or status projections.

Create a deployment JSON outside all governed Git worktrees with exactly these fields:

```json
{
  "repository_root": "D:\\CyberRiskBrain-aidp-infrastructure",
  "bind_host": "127.0.0.1",
  "bind_port": 8443,
  "public_origin": "https://127.0.0.1:8443",
  "issuer": "https://keycloak.example.invalid/realms/predatorai",
  "client_id": "aidp-product-owner",
  "audience": "aidp-product-owner",
  "policy_version": "product-owner-confirmation-v1",
  "tls_certificate": "C:\\ProgramData\\PredatorAI\\product-owner\\tls.crt",
  "tls_private_key": "C:\\ProgramData\\PredatorAI\\product-owner\\tls.key",
  "protected_secret_file": "C:\\ProgramData\\PredatorAI\\product-owner\\oidc-secret.json",
  "trusted_issuer_token_file": "C:\\ProgramData\\PredatorAI\\product-owner\\issuer-secret.json",
  "security_audit_file": "C:\\ProgramData\\PredatorAI\\product-owner\\security-audit.jsonl"
}
```

Optionally add `oidc_ca_bundle` for a private CA. The service refuses non-loopback bind addresses, non-HTTPS origins, missing protected files, unsafe protected-file placement/ACLs, unsupported DPAPI scope, wrong Windows principal, or invalid confirmation contexts.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\product-owner-confirmation\Start-ProductOwnerConfirmation.ps1 -ConfigPath C:\ProgramData\PredatorAI\product-owner\deployment.json
```

The launcher passes `ConfigPath` as an argument vector to `python -m aidp_orchestration.product_owner_service`; it does not interpolate the path into Python source. `PRODUCT_OWNER_CONFIRMATION_READY` is printed only after configuration validation, credential loading, confirmation-core composition, and TLS server construction succeed.

## Issue a Product Owner approval context

The issuance endpoint accepts only loopback callers that present the dedicated DPAPI-protected issuance credential:

```powershell
$token = '<plaintext loaded by the trusted local watcher/operator from the protected provider>'
Invoke-RestMethod -Method Post `
  -Uri https://127.0.0.1:8443/product-owner/issue `
  -Headers @{ Authorization = "Bearer $token" }
```

The response contains only locator/status data: task ID, approval-context ID, confirmation URL, expiry, and Architect review ID. It contains no nonce, token, client secret, or authentication proof. The browser follows `confirmation_url`, authenticates through Keycloak, and submits the existing nonce-bound Product Owner decision flow.
