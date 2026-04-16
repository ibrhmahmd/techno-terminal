"""
app/modules/notifications/dispatchers/email_dispatcher.py
────────────────────────────────────────────────────────
Gmail SMTP email dispatcher — implements IMessageDispatcher.

Uses Python stdlib smtplib (zero dependencies).
Architecture is abstract — swap for SendGrid/Resend by replacing this file only.
"""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Tuple

from app.core.config import settings

logger = logging.getLogger(__name__)


class GmailEmailDispatcher:
    """
    Sends emails via Gmail SMTP using App Password auth.

    Configuration via env vars:
        GMAIL_SENDER_ADDRESS
        GMAIL_APP_PASSWORD
    """

    SMTP_HOST = "smtp.gmail.com"
    SMTP_PORT = 465

    def send(
        self,
        recipient: str,
        body: str,
        subject: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send an HTML email.

        Args:
            recipient: Email address.
            body: HTML email body.
            subject: Email subject line.

        Returns:
            (True, None) on success, (False, error_message) on failure.
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or "Techno Kids Notification"
            msg["From"] = settings.gmail_sender_address
            msg["To"] = recipient
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP_SSL(self.SMTP_HOST, self.SMTP_PORT) as server:
                server.login(
                    settings.gmail_sender_address,
                    settings.gmail_app_password,
                )
                server.sendmail(
                    settings.gmail_sender_address,
                    recipient,
                    msg.as_string(),
                )

            logger.info("Email sent to %s — subject: %s", recipient, subject)
            return True, None

        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP auth failed: {e}"
            logger.error(error_msg)
            return False, error_msg

        except Exception as e:
            error_msg = f"Email send error: {type(e).__name__}: {e}"
            logger.error(error_msg)
            return False, error_msg
