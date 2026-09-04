"""Small server-rendered HTTP boundary for Product Owner confirmation."""

from __future__ import annotations

import html
import secrets
from http import HTTPStatus
from typing import Callable, Iterable, Mapping
from urllib.parse import parse_qs

from .contracts import ProductOwnerAcceptanceStatus, ProductOwnerOperation
from .product_owner_confirmation import ApprovalChallenge, ProductOwnerConfirmationCommand, ProductOwnerConfirmationService
from .product_owner_oidc import KeycloakOIDCClient, OIDCError, new_oidc_transaction
from .product_owner_web_session import ProductOwnerWebSession, ProductOwnerWebSessionStore


_SECURITY_HEADERS = [
    ("Cache-Control", "no-store"), ("Pragma", "no-cache"),
    ("Referrer-Policy", "no-referrer"), ("X-Content-Type-Options", "nosniff"),
    ("X-Frame-Options", "DENY"),
    ("Content-Security-Policy", "default-src 'none'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"),
]


class ProductOwnerHTTPApplication:
    """WSGI adapter. It can only display, authenticate, confirm through the core, or logout."""

    def __init__(self, *, oidc: KeycloakOIDCClient, sessions: ProductOwnerWebSessionStore,
                 confirmation_service: ProductOwnerConfirmationService,
                 challenge_resolver: Callable[[str], ApprovalChallenge], public_origin: str,
                 confirmation_path: str = "/product-owner/confirm", maximum_body_bytes: int = 8192) -> None:
        if not public_origin.startswith("https://") or public_origin.endswith("/"):
            raise ValueError("an exact HTTPS public origin is required")
        if not confirmation_path.startswith("/") or ".." in confirmation_path or maximum_body_bytes > 16_384:
            raise ValueError("unsafe HTTP adapter configuration")
        self.oidc, self.sessions, self.service = oidc, sessions, confirmation_service
        if self.oidc.config.redirect_uri != public_origin + confirmation_path + "/callback":
            raise ValueError("OIDC redirect URI does not match the exact callback")
        self.oidc.set_session_validator(lambda identifier: self.sessions.get(identifier, touch=False))
        self.challenge_resolver, self.public_origin = challenge_resolver, public_origin
        self.path, self.maximum_body_bytes = confirmation_path, maximum_body_bytes

    def __call__(self, environ: Mapping[str, object], start_response: Callable[..., object]) -> Iterable[bytes]:
        try:
            status, headers, body = self._dispatch(environ)
        except (KeyError, OSError, RuntimeError, TypeError, ValueError, PermissionError, OIDCError):
            status, headers, body = HTTPStatus.BAD_REQUEST, [], b"Request rejected"
        response_headers = _SECURITY_HEADERS + [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))] + headers
        start_response(f"{status.value} {status.phrase}", response_headers)
        return [body]

    def _dispatch(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        if environ.get("wsgi.url_scheme") != "https" or environ.get("HTTP_HOST") != self.public_origin.removeprefix("https://"):
            raise PermissionError
        if environ.get("HTTP_X_HTTP_METHOD_OVERRIDE") is not None:
            raise PermissionError
        method, path = environ.get("REQUEST_METHOD"), environ.get("PATH_INFO")
        if method == "GET" and path == self.path:
            return self._display(environ)
        if method == "GET" and path == self.path + "/login":
            return self._login(environ)
        if method == "GET" and path == self.path + "/callback":
            return self._callback(environ)
        if method == "POST" and path == self.path:
            return self._confirm(environ)
        if method == "POST" and path == self.path + "/logout":
            return self._logout(environ)
        return HTTPStatus.NOT_FOUND, [], b"Not found"

    def _display(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        query = self._parameters(str(environ.get("QUERY_STRING", "")), {"context"})
        context_id = self._one(query, "context", maximum=64)
        session = self._optional_session(environ)
        headers: list[tuple[str, str]] = []
        if session is None:
            challenge = self.challenge_resolver(context_id)
            if challenge.approval_context.approval_context_id != context_id:
                raise PermissionError
            session = self.sessions.create(challenge.approval_context, challenge.nonce)
            headers.append(("Set-Cookie", self._cookie(session.session_id)))
        elif session.approval_context.approval_context_id != context_id:
            raise PermissionError
        context = session.approval_context
        if session.proof is None:
            body = f'<h1>Product Owner confirmation</h1><a href="{self.path}/login">Authenticate</a>'
        else:
            csrf = self.sessions.issue_csrf(session.session_id)
            fields = (("Task", context.task_id), ("Repository", context.repository_identity),
                      ("Remote", context.repository_remote_identity), ("Product commit", context.product_commit),
                      ("Implementation", context.implementation_execution_id), ("Architect review", context.architect_review_id),
                      ("Architect result", context.architect_result_digest))
            summary = "".join(f"<dt>{html.escape(label)}</dt><dd>{html.escape(value)}</dd>" for label, value in fields)
            body = (f"<h1>Product Owner confirmation</h1><dl>{summary}</dl><form method=post action=\"{self.path}\">"
                    f'<input type=hidden name=csrf value="{html.escape(csrf)}"><button name=operation value=ACCEPT>Accept</button>'
                    '<textarea name=reason maxlength=2048></textarea><button name=operation value=REQUEST_REWORK>Request rework</button></form>'
                    f'<form method=post action="{self.path}/logout"><input type=hidden name=csrf value="{html.escape(csrf)}">'
                    '<button type=submit>Log out</button></form>')
        return HTTPStatus.OK, headers, self._html(body)

    def _login(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        self._require_empty_query(environ)
        session = self._require_session(environ)
        transaction = new_oidc_transaction()
        session.oidc_transaction = transaction
        return HTTPStatus.SEE_OTHER, [("Location", self.oidc.authorization_url(transaction))], b""

    def _callback(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        query = self._parameters(str(environ.get("QUERY_STRING", "")), {"code", "state"})
        code, state = self._one(query, "code", maximum=4096), self._one(query, "state", maximum=256)
        session = self._require_session(environ)
        transaction = session.oidc_transaction
        session.oidc_transaction = None
        if transaction is None or not secrets.compare_digest(transaction.state, state):
            raise PermissionError
        authenticated = self.sessions.rotate_authenticated(session.session_id, self.oidc.exchange_code(code=code, transaction=transaction))
        location = f"{self.path}?context={authenticated.approval_context.approval_context_id}"
        return HTTPStatus.SEE_OTHER, [("Location", location), ("Set-Cookie", self._cookie(authenticated.session_id))], b""

    def _confirm(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        self._require_origin(environ)
        form = self._form(environ)
        if set(form) - {"csrf", "operation", "reason"}:
            raise PermissionError
        csrf, operation_text = self._one(form, "csrf", maximum=256), self._one(form, "operation", maximum=32)
        session = self.sessions.consume_csrf(self._require_session(environ).session_id, csrf)
        if session.proof is None:
            raise PermissionError
        operation = ProductOwnerOperation(operation_text)
        reasons = form.get("reason", [])
        if len(reasons) > 1:
            raise PermissionError
        reason = reasons[0] if reasons and reasons[0].strip() else None
        if operation is ProductOwnerOperation.ACCEPT and reason is not None:
            raise PermissionError
        command = ProductOwnerConfirmationCommand(
            session.approval_context.approval_context_id, session.approval_nonce, operation, reason,
            self.sessions.command_id(session.session_id, operation.value, reason),
            "first-party-product-owner-web", session.proof,
        )
        result = self.service.confirm(command)
        session.csrf_tokens.clear()
        safe_status = html.escape(result.status.value)
        code = HTTPStatus.OK if result.status in {ProductOwnerAcceptanceStatus.ACCEPTED_PENDING_CONSUMPTION, ProductOwnerAcceptanceStatus.ALREADY_APPLIED} else HTTPStatus.FORBIDDEN
        return code, [], self._html(f"<h1>Confirmation result</h1><p>{safe_status}</p>")

    def _logout(self, environ: Mapping[str, object]) -> tuple[HTTPStatus, list[tuple[str, str]], bytes]:
        self._require_origin(environ)
        form = self._form(environ)
        if set(form) != {"csrf"}:
            raise PermissionError
        session = self._require_session(environ)
        self.sessions.consume_csrf(session.session_id, self._one(form, "csrf", maximum=256))
        self.oidc.revoke_session(session.session_id)
        self.sessions.revoke(session.session_id)
        return HTTPStatus.SEE_OTHER, [("Location", self.oidc.config.post_logout_redirect_uri),
            ("Set-Cookie", f"{self.sessions.COOKIE_NAME}=; {self.sessions.cookie_attributes}; Max-Age=0")], b""

    def _form(self, environ: Mapping[str, object]) -> dict[str, list[str]]:
        if environ.get("CONTENT_TYPE") != "application/x-www-form-urlencoded":
            raise PermissionError
        raw_length = environ.get("CONTENT_LENGTH", "")
        if not isinstance(raw_length, str) or not raw_length.isdigit() or int(raw_length) > self.maximum_body_bytes:
            raise PermissionError
        stream = environ.get("wsgi.input")
        if not hasattr(stream, "read"):
            raise PermissionError
        data = stream.read(int(raw_length) + 1)
        if len(data) != int(raw_length) or len(data) > self.maximum_body_bytes:
            raise PermissionError
        try:
            return self._parameters(data.decode("utf-8", "strict"), {"csrf", "operation", "reason"})
        except UnicodeDecodeError as exc:
            raise PermissionError from exc

    @staticmethod
    def _parameters(value: str, allowed: set[str]) -> dict[str, list[str]]:
        if len(value) > 8192 or ";" in value:
            raise PermissionError
        parsed = parse_qs(value, keep_blank_values=True, strict_parsing=True, max_num_fields=8)
        if set(parsed) - allowed:
            raise PermissionError
        return parsed

    @staticmethod
    def _one(values: Mapping[str, list[str]], name: str, *, maximum: int) -> str:
        found = values.get(name)
        if found is None or len(found) != 1 or not found[0] or len(found[0]) > maximum or "\r" in found[0] or "\n" in found[0]:
            raise PermissionError
        return found[0]

    def _require_origin(self, environ: Mapping[str, object]) -> None:
        if environ.get("HTTP_ORIGIN") != self.public_origin:
            raise PermissionError

    @staticmethod
    def _require_empty_query(environ: Mapping[str, object]) -> None:
        if environ.get("QUERY_STRING", ""):
            raise PermissionError

    def _optional_session(self, environ: Mapping[str, object]) -> ProductOwnerWebSession | None:
        prefix = self.sessions.COOKIE_NAME + "="
        values = [item[len(prefix):] for item in str(environ.get("HTTP_COOKIE", "")).split("; ") if item.startswith(prefix)]
        if len(values) != 1:
            return None
        try:
            return self.sessions.get(values[0])
        except PermissionError:
            return None

    def _require_session(self, environ: Mapping[str, object]) -> ProductOwnerWebSession:
        session = self._optional_session(environ)
        if session is None:
            raise PermissionError
        return session

    def _cookie(self, identifier: str) -> str:
        return f"{self.sessions.COOKIE_NAME}={identifier}; {self.sessions.cookie_attributes}"

    @staticmethod
    def _html(fragment: str) -> bytes:
        return ("<!doctype html><meta charset=utf-8>" + fragment).encode("utf-8")
