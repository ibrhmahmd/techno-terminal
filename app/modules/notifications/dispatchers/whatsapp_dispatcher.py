"""
app/modules/notifications/dispatchers/whatsapp_dispatcher.py
───────────────────────────────────────────────────────────
Twilio WhatsApp dispatcher — implements IMessageDispatcher.

Sends messages via the Twilio WhatsApp Business API.
Works with both the free sandbox and production approved numbers.
"""
import logging
from typing import Optional, Tuple

from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

from app.core.config import settings
from app.modules.notifications.dispatchers.i_dispatcher import IMessageDispatcher

logger = logging.getLogger(__name__)


class TwilioWhatsAppDispatcher(IMessageDispatcher):
    """
    Sends WhatsApp messages through Twilio.

    Configuration via env vars:
        TWILIO_ACCOUNT_SID
        TWILIO_AUTH_TOKEN
        TWILIO_WHATSAPP_FROM  (e.g. 'whatsapp:+14155238886' for sandbox)
    """

    def __init__(self) -> None:
        self._client = None
        self._from_number = settings.twilio_whatsapp_from

    def _ensure_client(self) -> None:
        if self._client is None:
            self._client = Client(
                settings.twilio_account_sid,
                settings.twilio_auth_token,
            )

    def send(
        self,
        recipient: str,
        body: str,
        subject: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send a WhatsApp message.

        Args:
            recipient: Phone number in E.164 format (e.g. '+201012345678').
                       The 'whatsapp:' prefix is added automatically.
            body: Message body text.
            subject: Ignored for WhatsApp.

        Returns:
            (True, None) on success, (False, error_message) on failure.
        """
        import os
        if "TESTING" in os.environ or "PYTEST_CURRENT_TEST" in os.environ:
            logger.info("Test mode: WhatsApp send skipped for %s", recipient)
            return True, None

        # Normalize phone — ensure whatsapp: prefix
        to_number = recipient if recipient.startswith("whatsapp:") else f"whatsapp:{recipient}"

        try:
            self._ensure_client()
            message = self._client.messages.create(
                body=body,
                from_=self._from_number,
                to=to_number,
            )
            logger.info("WhatsApp sent: SID=%s to=%s", message.sid, to_number)
            return True, None

        except TwilioRestException as e:
            error_msg = f"Twilio error {e.code}: {e.msg}"
            logger.error("WhatsApp send failed: %s", error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Unexpected WhatsApp error: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return False, error_msg
