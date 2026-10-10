"""Auth module ports (ADR-0007)."""

from typing import Protocol


class AuthNotifier(Protocol):
    """Port for sending admin login alerts.

    Implementations must not raise; failures are logged by the caller.
    """

    def admin_login(
        self,
        *,
        username: str,
        email: str,
        role: str,
        ip_address: str,
        user_agent: str,
        alert_reason: str,
    ) -> None: ...