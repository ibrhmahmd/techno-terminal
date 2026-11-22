"""Delivery allowlist (#290): when NOTIFICATION_ALLOWLIST is set, only listed contacts receive anything."""
import re

from app.core.config import settings


def _normalise(contact: str) -> str:
    value = contact.strip().lower().removeprefix("whatsapp:").strip()
    return value if "@" in value else re.sub(r"[\s\-()]", "", value)


def is_contact_allowed(contact: str) -> bool:
    entries = {_normalise(e) for e in settings.notification_allowlist.split(",") if e.strip()}
    return not entries or _normalise(contact) in entries
