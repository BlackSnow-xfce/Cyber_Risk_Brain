"""Fail-closed Keycloak OIDC adapter for Product Owner confirmation."""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Mapping, Protocol
from urllib.parse import urlencode, urlsplit

from .contracts import (
    AuthenticatedProductOwner, ProductOwnerApprovalContext,
    ProductOwnerAuthorizationEvidence, ProductOwnerOperation,
)


class OIDCError(RuntimeError):
    """A generic authentication failure safe to expose to adapter code."""


class ProtectedSecretProvider(Protocol):
    """Deployment-owned provider; environment and CLI providers are intentional omissions."""

    def client_secret(self, client_id: str) -> str: ...


class OIDCTransport(Protocol):
    def get_json(self, url: str) -> Mapping[str, object]: ...
    def post_form(self, url: str, form: Mapping[str, str], *, client_secret: str) -> Mapping[str, object]: ...


class RequestsOIDCTransport:
    def __init__(self, *, timeout_seconds: float = 5, verify: bool | str = True) -> None:
        if timeout_seconds <= 0 or verify is False:
            raise ValueError("TLS verification and a positive timeout are required")
        self.timeout_seconds, self.verify = timeout_seconds, verify

    def get_json(self, url: str) -> Mapping[str, object]:
        import requests

        response = requests.get(url, timeout=self.timeout_seconds, verify=self.verify)
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise OIDCError("identity dependency returned an invalid response")
        return value

    def post_form(self, url: str, form: Mapping[str, str], *, client_secret: str) -> Mapping[str, object]:
        import requests

        response = requests.post(
            url, data=form, auth=(form["client_id"], client_secret),
            timeout=self.timeout_seconds, verify=self.verify,
        )
        response.raise_for_status()
        value = response.json()
        if not isinstance(value, dict):
            raise OIDCError("identity dependency returned an invalid response")
        return value


@dataclass(frozen=True, slots=True)
class ProductOwnerOIDCConfig:
    issuer: str
    client_id: str
    audience: str
    redirect_uri: str
    post_logout_redirect_uri: str
    repository_identity: str
    policy_version: str
    role: str = "aidp-product-owner"
    algorithms: tuple[str, ...] = ("RS256",)
    clock_skew_seconds: int = 60
    maximum_authentication_age: timedelta = timedelta(minutes=5)
    totp_acr_values: tuple[str, ...] = ("urn:keycloak:acr:totp",)

    def __post_init__(self) -> None:
        urls = (self.issuer, self.redirect_uri, self.post_logout_redirect_uri)
        if any(not _is_exact_https_url(value) for value in urls):
            raise ValueError("OIDC and browser endpoints require HTTPS")
        if self.issuer.endswith("/") or not all((self.client_id, self.audience, self.repository_identity, self.policy_version)):
            raise ValueError("OIDC bindings must be exact and explicit")
        if (
            not self.algorithms
            or len(set(self.algorithms)) != len(self.algorithms)
            or any(not value.startswith(("RS", "ES", "PS")) for value in self.algorithms)
        ):
            raise ValueError("only explicit asymmetric ID-token algorithms are permitted")
        if not 0 <= self.clock_skew_seconds <= 60 or self.maximum_authentication_age > timedelta(minutes=5):
            raise ValueError("OIDC time limits exceed policy")


@dataclass(frozen=True, slots=True)
class OIDCTransaction:
    state: str
    nonce: str
    code_verifier: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class OIDCSessionProof:
    session_id: str
    subject: str
    access_token: str
    authenticated_at: datetime


def new_oidc_transaction(*, now: datetime | None = None) -> OIDCTransaction:
    return OIDCTransaction(secrets.token_urlsafe(32), secrets.token_urlsafe(64), secrets.token_urlsafe(64), now or datetime.now(timezone.utc))


class KeycloakOIDCClient:
    """Authorization-code/PKCE client and confirmation-time authority ports."""

    def __init__(self, config: ProductOwnerOIDCConfig, *, secrets_provider: ProtectedSecretProvider,
                 transport: OIDCTransport | None = None, clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        if secrets_provider is None:
            raise ValueError("a protected secret provider is required")
        self.config, self.secret_provider = config, secrets_provider
        self.transport, self.clock = transport or RequestsOIDCTransport(), clock
        self._metadata: Mapping[str, object] | None = None
        self._jwks: Mapping[str, object] | None = None
        self._active_sessions: dict[str, OIDCSessionProof] = {}
        self._session_validator: Callable[[str], None] | None = None

    def set_session_validator(self, validator: Callable[[str], None]) -> None:
        """Bind authorization to the adapter's current process-local session."""
        self._session_validator = validator

    def authorization_url(self, transaction: OIDCTransaction) -> str:
        metadata = self._discovery()
        endpoint = self._exact_https(metadata, "authorization_endpoint")
        challenge = base64.urlsafe_b64encode(hashlib.sha256(transaction.code_verifier.encode()).digest()).rstrip(b"=").decode()
        return endpoint + "?" + urlencode({
            "response_type": "code", "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri, "scope": "openid",
            "state": transaction.state, "nonce": transaction.nonce,
            "code_challenge": challenge, "code_challenge_method": "S256",
            "acr_values": " ".join(self.config.totp_acr_values),
        })

    def exchange_code(self, *, code: str, transaction: OIDCTransaction) -> OIDCSessionProof:
        if not code or len(code) > 4096 or self.clock() - transaction.created_at > timedelta(minutes=5):
            raise OIDCError("authentication failed")
        metadata = self._discovery()
        tokens = self.transport.post_form(self._exact_https(metadata, "token_endpoint"), {
            "grant_type": "authorization_code", "code": code, "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri, "code_verifier": transaction.code_verifier,
        }, client_secret=self._secret())
        id_token, access_token = tokens.get("id_token"), tokens.get("access_token")
        if not isinstance(id_token, str) or not isinstance(access_token, str):
            raise OIDCError("authentication failed")
        claims = self._decode(id_token)
        if claims.get("nonce") != transaction.nonce:
            raise OIDCError("authentication failed")
        subject, auth_time = self._identity_claims(claims)
        return OIDCSessionProof("", subject, access_token, auth_time)

    def authenticate(self, proof: object, context: ProductOwnerApprovalContext) -> AuthenticatedProductOwner:
        if not isinstance(proof, OIDCSessionProof):
            raise PermissionError("invalid authentication proof")
        claims = self._introspect(proof)
        subject, auth_time = self._identity_claims(claims)
        if subject != proof.subject or auth_time != proof.authenticated_at:
            raise PermissionError("session binding changed")
        self._active_sessions[proof.session_id] = proof
        principal = hashlib.sha256(f"{self.config.issuer}\0{subject}".encode()).hexdigest()
        return AuthenticatedProductOwner(principal, self.config.issuer, subject,
            hashlib.sha256(proof.session_id.encode()).hexdigest(), auth_time,
            "oidc-code-pkce-totp", str(claims.get("acr")), proof.session_id)

    def authorize(self, principal: AuthenticatedProductOwner, context: ProductOwnerApprovalContext,
                  operation: ProductOwnerOperation, *, at: datetime) -> ProductOwnerAuthorizationEvidence:
        if context.repository_identity != self.config.repository_identity or context.policy_version != self.config.policy_version:
            raise PermissionError("authorization binding mismatch")
        proof = self._active_sessions.get(principal.session_reference)
        if proof is None or self._session_validator is None:
            raise PermissionError("active browser session required")
        self._session_validator(principal.session_reference)
        claims = self._introspect(proof)
        subject, _ = self._identity_claims(claims)
        if subject != principal.subject:
            raise PermissionError("subject binding changed")
        return ProductOwnerAuthorizationEvidence(
            hashlib.sha256(f"{principal.principal_id}\0{context.approval_context_id}\0{operation.value}\0{at.isoformat()}".encode()).hexdigest(),
            principal.principal_id, operation, context.task_id, context.repository_identity,
            context.policy_version, at, min(context.expires_at, at + timedelta(minutes=5)),
        )

    def revoke_session(self, session_id: str) -> None:
        self._active_sessions.pop(session_id, None)

    def _introspect(self, proof: OIDCSessionProof) -> Mapping[str, object]:
        endpoint = self._exact_https(self._discovery(), "introspection_endpoint")
        claims = self.transport.post_form(endpoint, {"token": proof.access_token, "client_id": self.config.client_id}, client_secret=self._secret())
        if claims.get("active") is not True:
            raise PermissionError("inactive session")
        self._validate_common(claims)
        self._require_role_and_assurance(claims)
        return claims

    def _decode(self, token: str) -> Mapping[str, object]:
        try:
            import jwt

            header = jwt.get_unverified_header(token)
            if header.get("alg") not in self.config.algorithms or not isinstance(header.get("kid"), str):
                raise OIDCError("authentication failed")
            for refresh in (False, True):
                jwks = self._get_jwks(refresh=refresh)
                keys = [key for key in jwks.get("keys", []) if isinstance(key, dict) and key.get("kid") == header["kid"]]
                if len(keys) > 1:
                    raise OIDCError("authentication failed")
                if keys:
                    if keys[0].get("use", "sig") != "sig" or keys[0].get("alg", header["alg"]) != header["alg"]:
                        raise OIDCError("authentication failed")
                    public_key = jwt.PyJWK.from_dict(keys[0], algorithm=header["alg"]).key
                    claims = jwt.decode(token, public_key, algorithms=list(self.config.algorithms), audience=self.config.audience,
                                        issuer=self.config.issuer, leeway=self.config.clock_skew_seconds,
                                        options={"require": ["exp", "iat", "iss", "aud", "sub", "auth_time", "azp"]})
                    self._validate_common(claims)
                    self._require_role_and_assurance(claims)
                    return claims
            raise OIDCError("authentication failed")
        except (ImportError, KeyError, TypeError, ValueError) as exc:
            raise OIDCError("authentication failed") from exc
        except Exception as exc:
            # PyJWT deliberately remains an optional import until deployment
            # dependencies are installed; none of its detailed errors cross
            # the authentication boundary.
            raise OIDCError("authentication failed") from exc

    def _validate_common(self, claims: Mapping[str, object]) -> None:
        now = self.clock().timestamp()
        if claims.get("iss") != self.config.issuer or claims.get("azp") != self.config.client_id:
            raise PermissionError("identity binding mismatch")
        audience = claims.get("aud")
        if self.config.audience not in ((audience,) if isinstance(audience, str) else audience if isinstance(audience, list) else ()):
            raise PermissionError("audience mismatch")
        for name in ("exp", "iat", "auth_time"):
            if type(claims.get(name)) is not int:
                raise PermissionError("invalid time claim")
        skew = self.config.clock_skew_seconds
        if claims["exp"] <= now - skew or claims["iat"] > now + skew or claims["auth_time"] > now + skew:
            raise PermissionError("invalid token time")
        if "nbf" in claims and (type(claims["nbf"]) is not int or claims["nbf"] > now + skew):
            raise PermissionError("invalid token time")

    def _identity_claims(self, claims: Mapping[str, object]) -> tuple[str, datetime]:
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject or len(subject) > 255:
            raise PermissionError("subject missing")
        auth_time = datetime.fromtimestamp(float(claims["auth_time"]), timezone.utc)
        if self.clock() - auth_time > self.config.maximum_authentication_age:
            raise PermissionError("authentication is stale")
        return subject, auth_time

    def _require_role_and_assurance(self, claims: Mapping[str, object]) -> None:
        access = claims.get("resource_access")
        client = access.get(self.config.client_id) if isinstance(access, dict) else None
        roles = client.get("roles") if isinstance(client, dict) else None
        if not isinstance(roles, list) or self.config.role not in roles:
            raise PermissionError("dedicated role required")
        amr, acr = claims.get("amr"), claims.get("acr")
        if not isinstance(amr, list) or "otp" not in amr or acr not in self.config.totp_acr_values:
            raise PermissionError("TOTP assurance required")

    def _discovery(self) -> Mapping[str, object]:
        if self._metadata is None:
            self._metadata = self.transport.get_json(self.config.issuer + "/.well-known/openid-configuration")
            if self._metadata.get("issuer") != self.config.issuer:
                raise OIDCError("identity dependency is misconfigured")
        return self._metadata

    def _get_jwks(self, *, refresh: bool) -> Mapping[str, object]:
        if refresh or self._jwks is None:
            self._jwks = self.transport.get_json(self._exact_https(self._discovery(), "jwks_uri"))
        return self._jwks

    def _secret(self) -> str:
        secret = self.secret_provider.client_secret(self.config.client_id)
        if not isinstance(secret, str) or not secret.strip():
            raise OIDCError("protected credential unavailable")
        return secret

    def _exact_https(self, metadata: Mapping[str, object], field: str) -> str:
        value = metadata.get(field)
        if (
            not isinstance(value, str)
            or not _is_exact_https_url(value)
            or not value.startswith(self.config.issuer + "/")
        ):
            raise OIDCError("identity dependency is misconfigured")
        return value


def _is_exact_https_url(value: str) -> bool:
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
            and not parsed.fragment
            and not parsed.query
        )
    except ValueError:
        return False
