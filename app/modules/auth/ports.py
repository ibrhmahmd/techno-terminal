"""Auth module ports (ADR-0007)."""

from datetime import datetime
from typing import Optional, Protocol


class AuthNotifier(Protocol):
    """Port for auth emails: admin login alerts and user invites.

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

    def user_invited(
        self,
        *,
        email: str,
        role: str,
        register_url: str,
        expires_at: Optional[datetime],
        employee_id: Optional[int],
    ) -> None: ...
