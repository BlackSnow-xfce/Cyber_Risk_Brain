"""Production composition and HTTPS host for Product Owner confirmation."""

from __future__ import annotations

import json
import ssl
import threading
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import Callable, Iterable, Mapping
from urllib.parse import urlencode
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

from .product_owner_confirmation import ApprovalChallenge, ApprovalContextIssuer, ProductOwnerConfirmationService
from .product_owner_deployment import JsonLineSecurityAuditSink, ProductOwnerDeploymentConfig, WindowsDPAPISecretProvider
from .product_owner_http import ProductOwnerHTTPApplication
from .product_owner_oidc import KeycloakOIDCClient, RequestsOIDCTransport
from .product_owner_web_session import ProductOwnerWebSessionStore
from .repository import AIDPRepository
from .runtime import LocalRuntimeStore


@dataclass(frozen=True, slots=True)
class ProductOwnerConfirmationLocator:
    approval_context_id: str
    confirmation_url: str
    expires_at: str


class _ChallengeRegistry:
    def __init__(self) -> None:
        self._values: dict[str, ApprovalChallenge] = {}
        self._lock = threading.RLock()

    def add(self, challenge: ApprovalChallenge) -> ProductOwnerConfirmationLocator:
        with self._lock:
            self._purge()
            context = challenge.approval_context
            self._values[context.approval_context_id] = challenge
            return ProductOwnerConfirmationLocator(context.approval_context_id, "", context.expires_at.isoformat())

    def get(self, context_id: str) -> ApprovalChallenge:
        with self._lock:
            self._purge()
            value = self._values.get(context_id)
            if value is None:
                raise ValueError("approval context challenge unavailable")
            return value

    def remove(self, context_id: str) -> None:
        with self._lock:
            self._values.pop(context_id, None)

    def _purge(self) -> None:
        from .contracts import utc_now
        now = utc_now()
        expired = [key for key, value in self._values.items() if now >= value.approval_context.expires_at]
        for key in expired:
            del self._values[key]


class ProductOwnerServiceApplication:
    """Issuance/status shell around the hardened confirmation HTTP adapter."""

    def __init__(self, *, issuer: ApprovalContextIssuer, confirmation: ProductOwnerHTTPApplication,
                 registry: _ChallengeRegistry, public_origin: str) -> None:
        self.issuer = issuer
        self.confirmation = confirmation
        self.registry = registry
        self.public_origin = public_origin

    def __call__(self, environ: Mapping[str, object], start_response: Callable[..., object]) -> Iterable[bytes]:
        method = environ.get("REQUEST_METHOD")
        path = environ.get("PATH_INFO")
        if environ.get("wsgi.url_scheme") != "https":
            return self._response(start_response, HTTPStatus.BAD_REQUEST, {"status": "BLOCKED"})
        if method == "POST" and path == "/product-owner/issue":
            return self._issue(environ, start_response)
        if method == "GET" and path == "/product-owner/status":
            return self._status(environ, start_response)
        if method == "GET" and path == "/signed-out":
            return self._html(start_response, HTTPStatus.OK, b"<h1>Signed out</h1>")
        return self.confirmation(environ, start_response)

    def _issue(self, environ: Mapping[str, object], start_response: Callable[..., object]) -> Iterable[bytes]:
        if environ.get("CONTENT_LENGTH") not in {"", "0", None}:
            return self._response(start_response, HTTPStatus.BAD_REQUEST, {"status": "BLOCKED"})
        try:
            challenge = self.issuer.issue()
            context = challenge.approval_context
            self.registry.add(challenge)
            locator = self.public_origin + "/product-owner/confirm?" + urlencode({"context": context.approval_context_id})
            return self._response(start_response, HTTPStatus.CREATED, {
                "status": "WAITING_FOR_PRODUCT_OWNER",
                "task_id": context.task_id,
                "approval_context_id": context.approval_context_id,
                "confirmation_url": locator,
                "expires_at": context.expires_at.isoformat(),
                "architect_review_id": context.architect_review_id,
            })
        except (OSError, RuntimeError, ValueError):
            return self._response(start_response, HTTPStatus.CONFLICT, {"status": "BLOCKED"})

    def _status(self, environ: Mapping[str, object], start_response: Callable[..., object]) -> Iterable[bytes]:
        query = str(environ.get("QUERY_STRING", ""))
        if not query.startswith("context=") or "&" in query or ";" in query:
            return self._response(start_response, HTTPStatus.BAD_REQUEST, {"status": "BLOCKED"})
        context_id = query.removeprefix("context=")
        try:
            challenge = self.registry.get(context_id)
            context = challenge.approval_context
            locator = self.public_origin + "/product-owner/confirm?" + urlencode({"context": context.approval_context_id})
            return self._response(start_response, HTTPStatus.OK, {
                "status": "WAITING_FOR_PRODUCT_OWNER",
                "task_id": context.task_id,
                "approval_context_id": context.approval_context_id,
                "confirmation_url": locator,
                "expires_at": context.expires_at.isoformat(),
                "architect_review_id": context.architect_review_id,
            })
        except (OSError, RuntimeError, ValueError):
            return self._response(start_response, HTTPStatus.NOT_FOUND, {"status": "UNAVAILABLE"})

    @staticmethod
    def _response(start_response: Callable[..., object], status: HTTPStatus, value: dict[str, object]) -> list[bytes]:
        body = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
        start_response(f"{status.value} {status.phrase}", [
            ("Content-Type", "application/json; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
            ("X-Content-Type-Options", "nosniff"),
        ])
        return [body]

    @staticmethod
    def _html(start_response: Callable[..., object], status: HTTPStatus, body: bytes) -> list[bytes]:
        start_response(f"{status.value} {status.phrase}", [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
            ("Cache-Control", "no-store"),
        ])
        return [body]


class _QuietRequestHandler(WSGIRequestHandler):
    def get_environ(self):
        environ = super().get_environ()
        environ["wsgi.url_scheme"] = "https"
        environ["HTTPS"] = "on"
        return environ

    def log_message(self, format: str, *args: object) -> None:
        return


@dataclass(slots=True)
class ProductOwnerConfirmationRuntime:
    config: ProductOwnerDeploymentConfig
    application: ProductOwnerServiceApplication
    server: WSGIServer

    def serve_forever(self) -> None:
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()
        self.server.server_close()


def build_product_owner_confirmation_runtime(config_path: Path) -> ProductOwnerConfirmationRuntime:
    config = ProductOwnerDeploymentConfig.load(config_path)
    config.validate_files()
    repository = AIDPRepository(config.repository_root, task_namespace="infrastructure")
    runtime = LocalRuntimeStore.for_repository(repository.root)
    audit = JsonLineSecurityAuditSink(config.security_audit_file)
    secrets_provider = WindowsDPAPISecretProvider(config.protected_secret_file, expected_client_id=config.client_id)
    verify: bool | str = True if config.oidc_ca_bundle is None else str(config.oidc_ca_bundle)
    oidc = KeycloakOIDCClient(config.oidc_config(), secrets_provider=secrets_provider,
                              transport=RequestsOIDCTransport(verify=verify), audit=audit)
    sessions = ProductOwnerWebSessionStore()
    issuer = ApprovalContextIssuer(repository, runtime, policy_version=config.policy_version)
    confirmation_service = ProductOwnerConfirmationService(
        runtime, authenticator=oidc, authorizer=oidc, context_validator=issuer.revalidate,
    )
    registry = _ChallengeRegistry()
    confirmation = ProductOwnerHTTPApplication(
        oidc=oidc, sessions=sessions, confirmation_service=confirmation_service,
        challenge_resolver=registry.get, public_origin=config.public_origin, audit=audit,
    )
    application = ProductOwnerServiceApplication(
        issuer=issuer, confirmation=confirmation, registry=registry, public_origin=config.public_origin,
    )
    server = make_server(config.bind_host, config.bind_port, application, handler_class=_QuietRequestHandler)
    tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(certfile=str(config.tls_certificate), keyfile=str(config.tls_private_key))
    server.socket = tls.wrap_socket(server.socket, server_side=True)
    return ProductOwnerConfirmationRuntime(config, application, server)
