"""
app/modules/notifications/dispatchers/email_dispatcher.py
────────────────────────────────────────────────────────
Gmail SMTP email dispatcher — implements IMessageDispatcher.

Uses Python stdlib smtplib (zero dependencies).
Architecture is abstract — swap for SendGrid/Resend by replacing this file only.
"""
import asyncio
import logging
import smtplib
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import List, Optional, Tuple

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

    async def send(
        self,
        recipient: str,
        body: str,
        subject: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Send an HTML email with optional attachments.

        Args:
            recipient: Email address.
            body: HTML email body.
            subject: Email subject line.
            attachments: List of (filename, file_bytes, mimetype) tuples.

        Returns:
            (True, None) on success, (False, error_message) on failure.
        """
        try:
            # Create message container
            msg = MIMEMultipart("mixed")
            msg["Subject"] = subject or "Techno Kids Notification"
            msg["From"] = settings.gmail_sender_address
            msg["To"] = recipient

            # Attach HTML body
            msg.attach(MIMEText(body, "html"))

            # Attach files if provided
            if attachments:
                for filename, file_bytes, mimetype in attachments:
                    part = MIMEBase("application", mimetype)
                    part.set_payload(file_bytes)
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename=\"{filename}\"",
                    )
                    msg.attach(part)

            # Run blocking SMTP operations in thread pool
            def _send_email():
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

            await asyncio.to_thread(_send_email)

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
