"""
Mock dispatchers and repositories for notification testing.
Captures sent messages in-memory for assertion without real SMTP/Twilio.
"""
from datetime import datetime
from typing import Optional, Any
from dataclasses import dataclass, field


@dataclass
class CapturedEmail:
    recipient: str
    body: str
    subject: Optional[str]
    attachments: Optional[list] = None
    sent_at: datetime = field(default_factory=datetime.utcnow)


class MockEmailDispatcher:
    """Captures sent emails in-memory instead of sending via SMTP."""

    def __init__(self):
        self.sent_emails: list[CapturedEmail] = []

    async def send(self, recipient: str, body: str, subject: Optional[str] = None,
                   attachments: Optional[list] = None):
        self.sent_emails.append(CapturedEmail(
            recipient=recipient, body=body, subject=subject, attachments=attachments,
        ))
        return True, None

    def clear(self):
        self.sent_emails.clear()


class MockWhatsAppDispatcher:
    """Captures sent WhatsApp messages in-memory instead of sending via Twilio."""

    def __init__(self):
        self.sent_messages: list[dict] = []

    def send(self, recipient: str, body: str, subject: Optional[str] = None):
        self.sent_messages.append({
            "recipient": recipient, "body": body, "subject": subject,
            "sent_at": datetime.utcnow(),
        })
        return True, None

    def clear(self):
        self.sent_messages.clear()


class _MockLog:
    """Simple object with attribute access for mock notification logs."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _MockTemplate:
    """Simple object with attribute access for mock notification templates."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class MockNotificationRepository:
    """In-memory repository stub for isolated notification service testing."""

    def __init__(self, session=None):
        self._session = session
        self.logs: list[_MockLog] = []
        self.templates: dict[str, _MockTemplate] = {}

    def get_template_by_name(self, name: str) -> Optional[_MockTemplate]:
        return self.templates.get(name)

    def get_template_by_code(self, code: str) -> Optional[_MockTemplate]:
        for t in self.templates.values():
            if getattr(t, "code", None) == code:
                return t
        return None

    def get_template_by_id(self, template_id: int) -> Optional[_MockTemplate]:
        for t in self.templates.values():
            if getattr(t, "id", None) == template_id:
                return t
        return None

    def create_log(self, template_id=None, channel="EMAIL", recipient_type="ADDITIONAL",
                   recipient_id=0, recipient_contact="", body="", subject=None):
        log = _MockLog(
            id=len(self.logs) + 1,
            template_id=template_id, channel=channel, recipient_type=recipient_type,
            recipient_id=recipient_id, recipient_contact=recipient_contact,
            body=body, subject=subject, status="PENDING", error_message=None,
            retry_count=0, next_retry_at=None, sent_at=None,
            created_at=datetime.utcnow(),
        )
        self.logs.append(log)
        return log

    def update_log_status(self, log_id: int, status: str, error: Optional[str] = None):
        for log in self.logs:
            if log.id == log_id:
                log.status = status
                log.error_message = error
                if status == "SENT":
                    log.sent_at = datetime.utcnow()
                return

    def update_log_retry(self, log_id: int, retry_count: int, next_retry_at=None):
        for log in self.logs:
            if log.id == log_id:
                log.retry_count = retry_count
                log.next_retry_at = next_retry_at
                return

    def get_logs_for_retry(self, limit=10):
        return [log for log in self.logs if log.status == "FAILED" and log.retry_count < 3][:limit]

    def get_logs_due_for_retry(self, limit=10):
        now = datetime.utcnow()
        return [
            log for log in self.logs
            if log.status == "RETRYING" and log.next_retry_at is not None and log.next_retry_at <= now
        ][:limit]
