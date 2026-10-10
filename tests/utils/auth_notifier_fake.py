"""Test fake for AuthNotifier port."""

from dataclasses import dataclass, field
from typing import Optional
from app.modules.auth import AuthNotifier


@dataclass
class FakeAuthNotifier(AuthNotifier):
    """Records calls to admin_login for test assertions."""

    calls: list[dict] = field(default_factory=list)
    should_raise: bool = False
    raise_exception: Optional[Exception] = None

    def admin_login(
        self,
        *,
        username: str,
        email: str,
        role: str,
        ip_address: str,
        user_agent: str,
        alert_reason: str,
    ) -> None:
        if self.should_raise:
            raise self.raise_exception or RuntimeError("Notifier failure")
        self.calls.append({
            "username": username,
            "email": email,
            "role": role,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "alert_reason": alert_reason,
        })

    def reset(self) -> None:
        self.calls.clear()