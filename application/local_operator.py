from dataclasses import dataclass, field
from datetime import datetime, timezone
import secrets
from typing import Callable
from urllib.parse import urlsplit


HUNT_HYPOTHESIS_CREATE_PERMISSION = "hunt_hypothesis:create"
LOCAL_OPERATOR_PRINCIPAL_TYPE = "human/operator"
_KNOWN_PERMISSIONS = frozenset({HUNT_HYPOTHESIS_CREATE_PERMISSION})


class LocalOperatorConfigurationUnavailableError(RuntimeError):
    pass


class LocalOperatorConfigurationIntegrityError(RuntimeError):
    pass


class LocalOperatorAuthenticationError(RuntimeError):
    pass


class LocalOperatorAuthorizationError(RuntimeError):
    pass


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    principal_id: str
    display_name: str
    principal_type: str
    permissions: frozenset[str]


@dataclass(frozen=True)
class LocalOperatorConfiguration:
    principal_id: str
    display_name: str
    token: str = field(repr=False)
    permissions: frozenset[str]
    allowed_origins: tuple[str, ...]


@dataclass(frozen=True)
class AuthorizationDecision:
    principal_id: str
    operation: str
    timestamp: datetime
    outcome: str


class LocalOperatorAuthenticator:
    def __init__(self, configuration: LocalOperatorConfiguration) -> None:
        self._configuration = configuration

    @classmethod
    def from_values(
        cls,
        *,
        mode_enabled: str | None,
        principal_id: str | None,
        display_name: str | None,
        token: str | None,
        permissions: str | None,
        allowed_origins: str | None,
    ) -> "LocalOperatorAuthenticator":
        if mode_enabled is None or mode_enabled.strip().lower() == "false":
            raise LocalOperatorConfigurationUnavailableError(
                "Local Operator mode is not configured."
            )
        if mode_enabled.strip().lower() != "true":
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator mode configuration is invalid."
            )
        values = (principal_id, display_name, token, permissions, allowed_origins)
        if any(value is None for value in values):
            raise LocalOperatorConfigurationUnavailableError(
                "Local Operator configuration is incomplete."
            )
        assert principal_id is not None
        assert display_name is not None
        assert token is not None
        assert permissions is not None
        assert allowed_origins is not None
        if not principal_id.strip() or not display_name.strip() or not token:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator identity configuration is invalid."
            )
        if len(token.encode("utf-8")) < 32:
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator credential configuration is invalid."
            )
        return cls(
            LocalOperatorConfiguration(
                principal_id=principal_id.strip(),
                display_name=display_name.strip(),
                token=token,
                permissions=_parse_permissions(permissions),
                allowed_origins=parse_local_operator_allowed_origins(allowed_origins),
            )
        )

    def authenticate(self, authorization: str | None) -> AuthenticatedPrincipal:
        if authorization is None:
            raise LocalOperatorAuthenticationError("Authentication is required.")
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0] != "Bearer" or not parts[1]:
            raise LocalOperatorAuthenticationError("Authentication is invalid.")
        if not secrets.compare_digest(
            parts[1].encode("utf-8"),
            self._configuration.token.encode("utf-8"),
        ):
            raise LocalOperatorAuthenticationError("Authentication is invalid.")
        return AuthenticatedPrincipal(
            principal_id=self._configuration.principal_id,
            display_name=self._configuration.display_name,
            principal_type=LOCAL_OPERATOR_PRINCIPAL_TYPE,
            permissions=self._configuration.permissions,
        )


class HuntHypothesisWriteAuthority:
    def __init__(
        self,
        clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        self._clock = clock

    def evaluate(self, principal: AuthenticatedPrincipal) -> AuthorizationDecision:
        timestamp = self._clock()
        if timestamp.tzinfo is None:
            raise LocalOperatorConfigurationIntegrityError(
                "The authorization clock must be timezone-aware."
            )
        allowed = HUNT_HYPOTHESIS_CREATE_PERMISSION in principal.permissions
        return AuthorizationDecision(
            principal_id=principal.principal_id,
            operation=HUNT_HYPOTHESIS_CREATE_PERMISSION,
            timestamp=timestamp,
            outcome="allowed" if allowed else "denied",
        )

    def require(self, principal: AuthenticatedPrincipal) -> AuthorizationDecision:
        decision = self.evaluate(principal)
        if decision.outcome != "allowed":
            raise LocalOperatorAuthorizationError(
                "The authenticated principal is not authorized."
            )
        return decision


def parse_local_operator_allowed_origins(raw: str) -> tuple[str, ...]:
    entries = raw.split(",")
    if not entries or any(not entry.strip() for entry in entries):
        raise LocalOperatorConfigurationIntegrityError(
            "Local Operator allowed origins are invalid."
        )
    origins = tuple(entry.strip() for entry in entries)
    if len(set(origins)) != len(origins):
        raise LocalOperatorConfigurationIntegrityError(
            "Local Operator allowed origins contain duplicates."
        )
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            origin == "*"
            or parsed.scheme not in {"http", "https"}
            or parsed.hostname not in {"localhost", "127.0.0.1"}
            or parsed.port is None
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise LocalOperatorConfigurationIntegrityError(
                "Local Operator allowed origins are invalid."
            )
    return origins


def configured_local_operator_origins(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return ()
    try:
        return parse_local_operator_allowed_origins(raw)
    except LocalOperatorConfigurationIntegrityError:
        # Keep cross-origin access disabled. The authentication dependency
        # reports the invalid configuration without exposing its contents.
        return ()


def _parse_permissions(raw: str) -> frozenset[str]:
    if raw == "":
        return frozenset()
    entries = tuple(entry.strip() for entry in raw.split(","))
    if any(not entry for entry in entries) or len(set(entries)) != len(entries):
        raise LocalOperatorConfigurationIntegrityError(
            "Local Operator permissions are invalid."
        )
    if not set(entries).issubset(_KNOWN_PERMISSIONS):
        raise LocalOperatorConfigurationIntegrityError(
            "Local Operator permissions are invalid."
        )
    return frozenset(entries)
