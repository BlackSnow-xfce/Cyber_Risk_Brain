# Product Owner confirmation boundary

This deployment hosts the existing Product Owner confirmation core behind a
first-party HTTPS service.

## Required administrator provisioning

Import `keycloak-realm.template.json`. The realm binds
`aidp-product-owner-browser` as its browser flow and requires both
username/password and OTP executions. The client remains confidential,
requires PKCE S256, the dedicated `aidp-product-owner` role, and the approved
TOTP ACR.

Create a TLS certificate/key pair for the configured `public_origin`. The
deployment configuration, TLS private key, protected credentials, their
provisioning evidence, and audit destination must be outside every governed
Git worktree and Git repository. The service rejects reparse-point traversal,
unsafe ownership, and writable ACLs outside the explicit service/SYSTEM/local
Administrators allowlist.

The deployment JSON must be outside all governed Git worktrees and contain
exactly these required fields (plus optional `oidc_ca_bundle`):

```json
{
  "repository_root": "D:\\CyberRiskBrain-aidp-infrastructure",
  "bind_host": "127.0.0.1",
  "bind_port": 8443,
  "public_origin": "https://aidp-confirmation.example.invalid",
  "issuer": "https://keycloak.example.invalid/realms/predatorai",
  "client_id": "aidp-product-owner",
  "audience": "aidp-product-owner",
  "policy_version": "product-owner-confirmation-v1",
  "service_principal_sid": "<exact Windows service-account SID>",
  "tls_certificate": "C:\\ProgramData\\PredatorAI\\product-owner\\tls.crt",
  "tls_private_key": "C:\\ProgramData\\PredatorAI\\product-owner\\tls.key",
  "protected_secret_file": "C:\\ProgramData\\PredatorAI\\product-owner\\oidc-secret.json",
  "trusted_issuer_token_file": "C:\\ProgramData\\PredatorAI\\product-owner\\issuer-secret.json",
  "security_audit_file": "C:\\ProgramData\\PredatorAI\\product-owner\\security-audit.jsonl"
}
```

Provision both credentials while logged on as the exact configured service
principal. Input is read twice from the protected console; plaintext is not a
command-line argument, environment variable, URL, log entry, or repository
file:

```powershell
python -m aidp_orchestration.product_owner_deployment provision --config C:\ProgramData\PredatorAI\product-owner\deployment.json --credential oidc-client
python -m aidp_orchestration.product_owner_deployment provision --config C:\ProgramData\PredatorAI\product-owner\deployment.json --credential trusted-issuer
```

The governed provisioner calls current-user `CryptProtectData` with flags zero,
applies and verifies the explicit ACL allowlist, and writes an
`aidp-dpapi-secret-v4` artifact plus an adjacent immutable-binding
`.provisioning.json` record. Runtime accepts only artifacts whose exact digest,
client identity, and service SID match that protected provisioning evidence.

Windows DPAPI does not expose the original protection flag during decryption.
The system therefore does **not** claim cryptographic machine-scope detection:
the authority boundary is the governed flags-zero creation path, execution as
the exact configured SID, and protected ACL custody of both files. A copied,
hand-built, relabelled, or legacy bare DPAPI artifact has no trusted
provisioning evidence and fails closed.

The plaintext values and generated protected files must never be placed in
Git, deployment JSON, ordinary environment variables, logs, or status
projections.

## Start

```powershell
powershell -ExecutionPolicy Bypass -File .\deploy\product-owner-confirmation\Start-ProductOwnerConfirmation.ps1 -ConfigPath C:\ProgramData\PredatorAI\product-owner\deployment.json
```

The launcher passes `ConfigPath` as an argument vector to
`python -m aidp_orchestration.product_owner_service`; it does not interpolate
the path into Python source. `PRODUCT_OWNER_CONFIRMATION_READY` is printed only
after fail-closed configuration, provisioning evidence, credential, OIDC, and
TLS validation succeeds.
