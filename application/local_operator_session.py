from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import re
import secrets
import threading
from typing import Callable
from urllib.parse import urlsplit

from application.local_operator import (
    AuthenticatedPrincipal,
    LocalOperatorConfigurationIntegrityError,
    LocalOperatorConfigurationUnavailableError,
)


LOCAL_OPERATOR_BACKEND_HOST = "127.0.0.1:8000"
_COOKIE_NAME = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class LocalOperatorSessionAuthenticationError(RuntimeError):
    pass


class LocalOperatorSessionCsrfError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class LocalOperatorSessionConfiguration:
    lifetime_seconds: int
    cookie_secure: bool
    cookie_name: str
    frontend_origin: str

    @classmethod
    def from_values(
        cls,
        *,
        enabled: str | None,
        lifetime_seconds: str | None,
        cookie_secure: str | None,
        cookie_name: str | None,
        allowed_origins: tuple[str, ...],
    ) -> "LocalOperatorSessionConfiguration":
        if enabled is None or enabled.strip().lower() == "false":
            raise LocalOperatorConfigurationUnavailableError(
                "Local Operator browser sessions are not configured."
            )
        if enabled.strip().lower() != "true":
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session enablement is invalid."
            )
        if lifetime_seconds is None or cookie_secure is None or cookie_name is None:
            raise LocalOperatorConfigurationUnavailableError(
                "Local Operator browser session configuration is incomplete."
            )
        try:
            lifetime = int(lifetime_seconds)
        except ValueError as error:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session lifetime is invalid."
            ) from error
        if lifetime < 60 or lifetime > 86400:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session lifetime is invalid."
            )
        secure_value = cookie_secure.strip().lower()
        if secure_value not in {"true", "false"}:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session cookie security is invalid."
            )
        if not _COOKIE_NAME.fullmatch(cookie_name):
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session cookie name is invalid."
            )
        if len(allowed_origins) != 1:
            raise LocalOperatorConfigurationIntegrityError(
                "Exactly one Local Operator browser origin is required."
            )
        origin = allowed_origins[0]
        secure = secure_value == "true"
        parsed_origin = urlsplit(origin)
        if not secure and (
            parsed_origin.scheme != "http"
            or parsed_origin.hostname not in {"127.0.0.1", "localhost"}
        ):
            raise LocalOperatorConfigurationIntegrityError(
                "Insecure cookies are permitted only for loopback HTTP."
            )
        return cls(
            lifetime_seconds=lifetime,
            cookie_secure=secure,
            cookie_name=cookie_name,
            frontend_origin=origin,
        )


@dataclass(frozen=True, slots=True)
class LocalOperatorBrowserSession:
    principal_id: str
    origin: str
    issued_at: datetime
    expires_at: datetime
    csrf_digest: bytes


@dataclass(frozen=True, slots=True)
class CreatedLocalOperatorSession:
    session_id: str
    expires_at: datetime


class LocalOperatorSessionStore:
    """Single-process, single-session local operator store."""

    def __init__(
        self,
        configuration: LocalOperatorSessionConfiguration,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        self.configuration = configuration
        self._clock = clock
        self._token_factory = token_factory
        self._lock = threading.Lock()
        self._session_digest: bytes | None = None
        self._session: LocalOperatorBrowserSession | None = None

    def create(self, principal: AuthenticatedPrincipal) -> CreatedLocalOperatorSession:
        session_id = self._fresh_token()
        issued_at = self._now()
        expires_at = issued_at + timedelta(
            seconds=self.configuration.lifetime_seconds
        )
        session = LocalOperatorBrowserSession(
            principal_id=principal.principal_id,
            origin=self.configuration.frontend_origin,
            issued_at=issued_at,
            expires_at=expires_at,
            csrf_digest=b"",
        )
        with self._lock:
            self._session_digest = _digest(session_id)
            self._session = session
        return CreatedLocalOperatorSession(session_id, expires_at)

    def resolve(
        self, session_id: str | None, principal: AuthenticatedPrincipal
    ) -> LocalOperatorBrowserSession:
        with self._lock:
            return self._resolve_locked(session_id, principal)

    def resolve_candidates(
        self, session_ids: tuple[str, ...], principal: AuthenticatedPrincipal
    ) -> tuple[str, LocalOperatorBrowserSession]:
        candidates = tuple(dict.fromkeys(session_ids))
        with self._lock:
            matches = tuple(
                candidate
                for candidate in candidates
                if self._matches_active_session_locked(candidate, principal)
            )
            if len(matches) != 1:
                raise LocalOperatorSessionAuthenticationError(
                    "A valid Local Operator browser session is required."
                )
            session_id = matches[0]
            return session_id, self._resolve_locked(session_id, principal)

    def issue_csrf(
        self, session_id: str, principal: AuthenticatedPrincipal
    ) -> tuple[LocalOperatorBrowserSession, str]:
        csrf_token = self._fresh_token()
        with self._lock:
            session = self._resolve_locked(session_id, principal)
            updated = LocalOperatorBrowserSession(
                principal_id=session.principal_id,
                origin=session.origin,
                issued_at=session.issued_at,
                expires_at=session.expires_at,
                csrf_digest=_digest(csrf_token),
            )
            self._session = updated
        return updated, csrf_token

    def require_mutation(
        self,
        session_id: str | None,
        principal: AuthenticatedPrincipal,
        *,
        origin: str | None,
        csrf_token: str | None,
    ) -> LocalOperatorBrowserSession:
        with self._lock:
            session = self._resolve_locked(session_id, principal)
            if origin != session.origin or not csrf_token or not session.csrf_digest:
                raise LocalOperatorSessionCsrfError(
                    "Local Operator request verification failed."
                )
            if not secrets.compare_digest(_digest(csrf_token), session.csrf_digest):
                raise LocalOperatorSessionCsrfError(
                    "Local Operator request verification failed."
                )
            return session

    def revoke(self, session_id: str | None) -> None:
        if not session_id:
            return
        supplied = _digest(session_id)
        with self._lock:
            if self._session_digest is not None and secrets.compare_digest(
                supplied, self._session_digest
            ):
                self._session_digest = None
                self._session = None

    def _fresh_token(self) -> str:
        token = self._token_factory()
        if not isinstance(token, str) or len(token.encode("utf-8")) < 32:
            raise LocalOperatorConfigurationIntegrityError(
                "Secure Local Operator session token generation failed."
            )
        return token

    def _resolve_locked(
        self, session_id: str | None, principal: AuthenticatedPrincipal
    ) -> LocalOperatorBrowserSession:
        if not session_id:
            raise LocalOperatorSessionAuthenticationError(
                "A valid Local Operator browser session is required."
            )
        supplied = _digest(session_id)
        if (
            self._session_digest is None
            or self._session is None
            or not secrets.compare_digest(supplied, self._session_digest)
            or self._session.principal_id != principal.principal_id
        ):
            raise LocalOperatorSessionAuthenticationError(
                "A valid Local Operator browser session is required."
            )
        if self._now() >= self._session.expires_at:
            self._session_digest = None
            self._session = None
            raise LocalOperatorSessionAuthenticationError(
                "The Local Operator browser session has expired."
            )
        return self._session

    def _matches_active_session_locked(
        self, session_id: str, principal: AuthenticatedPrincipal
    ) -> bool:
        return bool(
            session_id
            and self._session_digest is not None
            and self._session is not None
            and secrets.compare_digest(_digest(session_id), self._session_digest)
            and self._session.principal_id == principal.principal_id
        )

    def _now(self) -> datetime:
        value = self._clock()
        if value.tzinfo is None:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator session clock must be timezone-aware."
            )
        return value


def _digest(value: str) -> bytes:
    return hashlib.sha256(value.encode("utf-8")).digest()
