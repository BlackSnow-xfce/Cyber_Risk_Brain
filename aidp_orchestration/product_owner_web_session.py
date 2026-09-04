"""Bounded, opaque, memory-only Product Owner browser sessions."""

from __future__ import annotations

import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable

from .contracts import ProductOwnerApprovalContext
from .product_owner_oidc import OIDCSessionProof, OIDCTransaction


@dataclass(slots=True)
class ProductOwnerWebSession:
    session_id: str
    created_at: datetime
    last_seen_at: datetime
    approval_context: ProductOwnerApprovalContext
    approval_nonce: str
    oidc_transaction: OIDCTransaction | None = None
    proof: OIDCSessionProof | None = None
    csrf_tokens: set[str] = field(default_factory=set)
    confirmation_payload: tuple[str, str | None] | None = None
    confirmation_command_id: str | None = None


class ProductOwnerWebSessionStore:
    """Process-local authority deliberately lost on restart."""

    COOKIE_NAME = "__Host-aidp_product_owner"
    COOKIE_PATH = "/"

    def __init__(self, *, absolute_lifetime: timedelta = timedelta(minutes=15),
                 idle_lifetime: timedelta = timedelta(minutes=5), maximum_sessions: int = 1024,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)) -> None:
        if (
            absolute_lifetime <= timedelta(0)
            or idle_lifetime <= timedelta(0)
            or absolute_lifetime > timedelta(minutes=15)
            or idle_lifetime > timedelta(minutes=5)
            or not 1 <= maximum_sessions <= 4096
        ):
            raise ValueError("session limits exceed policy")
        self.absolute_lifetime, self.idle_lifetime = absolute_lifetime, idle_lifetime
        self.maximum_sessions, self.clock = maximum_sessions, clock
        self._sessions: dict[str, ProductOwnerWebSession] = {}
        self._lock = threading.RLock()

    @property
    def cookie_attributes(self) -> str:
        return f"Path={self.COOKIE_PATH}; Secure; HttpOnly; SameSite=Strict"

    def create(self, context: ProductOwnerApprovalContext, approval_nonce: str) -> ProductOwnerWebSession:
        if len(approval_nonce) < 32 or len(approval_nonce) > 256 or "\r" in approval_nonce or "\n" in approval_nonce:
            raise ValueError("invalid approval transaction")
        with self._lock:
            self._purge()
            if len(self._sessions) >= self.maximum_sessions:
                raise RuntimeError("session capacity unavailable")
            now, identifier = self.clock(), secrets.token_urlsafe(32)
            session = ProductOwnerWebSession(identifier, now, now, context, approval_nonce)
            self._sessions[identifier] = session
            return session

    def get(self, identifier: str, *, touch: bool = True) -> ProductOwnerWebSession:
        with self._lock:
            self._purge()
            session = self._sessions.get(identifier)
            if session is None:
                raise PermissionError("authentication required")
            if touch:
                session.last_seen_at = self.clock()
            return session

    def rotate_authenticated(self, identifier: str, proof: OIDCSessionProof) -> ProductOwnerWebSession:
        with self._lock:
            old = self.get(identifier, touch=False)
            del self._sessions[identifier]
            new_id = secrets.token_urlsafe(32)
            proof = OIDCSessionProof(new_id, proof.subject, proof.access_token, proof.authenticated_at)
            now = self.clock()
            session = ProductOwnerWebSession(new_id, old.created_at, now, old.approval_context, old.approval_nonce, proof=proof)
            self._sessions[new_id] = session
            return session

    def issue_csrf(self, identifier: str) -> str:
        with self._lock:
            session = self.get(identifier)
            token = secrets.token_urlsafe(32)
            session.csrf_tokens.clear()
            session.csrf_tokens.add(token)
            return token

    def consume_csrf(self, identifier: str, token: str) -> ProductOwnerWebSession:
        with self._lock:
            session = self.get(identifier)
            matching = next((item for item in session.csrf_tokens if secrets.compare_digest(item, token)), None)
            if matching is None:
                raise PermissionError("invalid request")
            session.csrf_tokens.remove(matching)
            return session

    def revoke(self, identifier: str) -> None:
        with self._lock:
            self._sessions.pop(identifier, None)

    def command_id(self, identifier: str, operation: str, reason: str | None) -> str:
        """Return one idempotency identity bound to an immutable browser payload."""
        with self._lock:
            session = self.get(identifier)
            payload = (operation, reason)
            if session.confirmation_payload is not None and session.confirmation_payload != payload:
                raise PermissionError("confirmation transaction already bound")
            if session.confirmation_command_id is None:
                session.confirmation_payload = payload
                session.confirmation_command_id = secrets.token_urlsafe(32)
            return session.confirmation_command_id

    def _purge(self) -> None:
        now = self.clock()
        expired = [key for key, value in self._sessions.items()
                   if now - value.created_at >= self.absolute_lifetime or now - value.last_seen_at >= self.idle_lifetime
                   or now >= value.approval_context.expires_at]
        for key in expired:
            del self._sessions[key]
