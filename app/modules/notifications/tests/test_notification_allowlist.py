"""NOTIFICATION_ALLOWLIST (#290): nothing is delivered to a contact that is not listed."""
from unittest.mock import MagicMock

import pytest

from app.core.config import settings
from app.modules.notifications.dispatchers import email_dispatcher, whatsapp_dispatcher
from app.modules.notifications.dispatchers.allowlist import is_contact_allowed
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.dispatchers.whatsapp_dispatcher import TwilioWhatsAppDispatcher


def _allow(monkeypatch, value):
    monkeypatch.setattr(settings, "notification_allowlist", value)


@pytest.mark.parametrize("value", ["", "   "])
def test_empty_allowlist_allows_everything(monkeypatch, value):
    _allow(monkeypatch, value)
    assert is_contact_allowed("anyone@example.com")


def test_email_is_case_insensitive(monkeypatch):
    _allow(monkeypatch, " Owner@Example.com ")
    assert is_contact_allowed("owner@example.COM")


def test_phone_ignores_spaces_dashes_parens_and_whatsapp_prefix(monkeypatch):
    _allow(monkeypatch, "+20 101-234 (5678)")
    assert is_contact_allowed("whatsapp:+201012345678")


def test_not_listed_is_blocked(monkeypatch):
    _allow(monkeypatch, "owner@example.com")
    assert not is_contact_allowed("other@example.com")
    assert not is_contact_allowed("+201012345678")


def test_multiple_entries(monkeypatch):
    _allow(monkeypatch, "owner@example.com, +201012345678")
    assert is_contact_allowed("owner@example.com")
    assert is_contact_allowed("whatsapp:+201012345678")
    assert not is_contact_allowed("x@example.com")


@pytest.fixture
def smtp(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(email_dispatcher.smtplib, "SMTP_SSL", mock)
    return mock


@pytest.mark.real_dispatchers
@pytest.mark.anyio
async def test_email_not_listed_is_suppressed(monkeypatch, smtp):
    _allow(monkeypatch, "owner@example.com")  # test mode rewrites the recipient to fallback_email
    ok, reason = await GmailEmailDispatcher().send("x@example.com", "<p>hi</p>", "s")
    assert (ok, reason.startswith("suppressed")) == (False, True)
    smtp.assert_not_called()


@pytest.mark.real_dispatchers
@pytest.mark.anyio
async def test_email_listed_is_sent(monkeypatch, smtp):
    _allow(monkeypatch, settings.fallback_email)
    assert await GmailEmailDispatcher().send("x@example.com", "<p>hi</p>", "s") == (True, None)
    smtp.assert_called_once()


@pytest.mark.real_dispatchers
@pytest.mark.anyio
async def test_email_empty_allowlist_is_sent(monkeypatch, smtp):
    _allow(monkeypatch, "")
    assert await GmailEmailDispatcher().send("x@example.com", "<p>hi</p>", "s") == (True, None)
    smtp.assert_called_once()


@pytest.mark.real_dispatchers
def test_whatsapp_not_listed_is_suppressed(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(whatsapp_dispatcher, "Client", client)
    _allow(monkeypatch, "+201000000000")
    ok, reason = TwilioWhatsAppDispatcher().send("+201012345678", "hi")
    assert (ok, reason.startswith("suppressed")) == (False, True)
    client.assert_not_called()
