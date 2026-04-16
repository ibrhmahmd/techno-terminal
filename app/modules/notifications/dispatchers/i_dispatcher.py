"""
app/modules/notifications/dispatchers/i_dispatcher.py
────────────────────────────────────────────────────
Abstract message dispatcher interface.

Any new channel (Telegram, Push, etc.) implements this protocol.
Swap dispatchers without touching NotificationService.
"""
from typing import Protocol, Optional, Tuple, runtime_checkable


@runtime_checkable
class IMessageDispatcher(Protocol):
    """
    Contract for all outbound message dispatchers.

    Returns:
        (success: bool, error_message: str | None)
    Never raises — errors are returned, not thrown.
    """

    def send(
        self,
        recipient: str,
        body: str,
        subject: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Dispatch a message to the given recipient."""
        ...
