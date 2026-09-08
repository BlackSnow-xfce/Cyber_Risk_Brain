# Product Owner confirmation boundary

This deployment hosts the existing Product Owner confirmation core behind a first-party HTTPS service.

## Required administrator provisioning

Create a dedicated Keycloak confidential client from `keycloak-realm.template.json`, require the dedicated `aidp-product-owner` client role and TOTP MFA, and set exact HTTPS redirect/logout URIs.

Create a TLS certificate/key pair for the configured `public_origin` and store them outside Git.

Create the Keycloak client secret as a Windows DPAPI-protected JSON document outside Git:

```json
{"schema_version":"aidp-dpapi-secret-v1","client_id":"aidp-product-owner","ciphertext":"<base64 DPAPI ciphertext>"}
```

The plaintext client secret must never be placed in Git, the deployment JSON, command-line arguments, or ordinary environment variables.

Create a deployment JSON outside Git with exactly these fields:

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
  "security_audit_file": "C:\\ProgramData\\PredatorAI\\product-owner\\security-audit.jsonl"
}
```

Optionally add `oidc_ca_bundle` for a private CA. The service refuses non-loopback bind addresses, missing TLS/credential files, non-HTTPS public origins, unknown configuration fields, missing trusted identity configuration, or unvalidated confirmation contexts.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\product-owner-confirmation\Start-ProductOwnerConfirmation.ps1 -ConfigPath C:\ProgramData\PredatorAI\product-owner\deployment.json
```

The process prints `PRODUCT_OWNER_CONFIRMATION_READY` only after configuration validation, DPAPI provider construction, confirmation-core composition, and TLS server construction succeed.

## Issue a Product Owner approval context

From the trusted local host:

```powershell
Invoke-RestMethod -Method Post -Uri https://127.0.0.1:8443/product-owner/issue
```

The response contains only locator/status data: task ID, approval-context ID, confirmation URL, expiry, and Architect review ID. The browser follows `confirmation_url`, authenticates through Keycloak, and submits the existing nonce-bound Product Owner decision flow.
