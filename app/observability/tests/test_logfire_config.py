"""
Regression tests for Logfire observability wiring.

Locks in the fix replaced: configure_logging() uses basicConfig(force=True),
which wipes every root logger handler — including the LogfireLoggingHandler
that configure_logfire() attaches. create_app() must run configure_logging()
BEFORE configure_logfire() so application logs actually reach Logfire.
"""
import logging

import logfire

from app.api.main import configure_logfire
from app.core.config import configure_logging, settings


def test_logfire_handler_survives_configure_logging():
    configure_logging(settings)
    configure_logfire()

    assert any(
        isinstance(handler, logfire.LogfireLoggingHandler)
        for handler in logging.getLogger().handlers
    )

def test_logfire_never_sends_under_tests():
    """#145: test runs must not ship telemetry, even when the env file has a token."""
    configure_logfire()

    assert logfire.DEFAULT_LOGFIRE_INSTANCE.config.send_to_logfire is False


def test_logfire_without_token_starts_and_does_not_send(monkeypatch):
    """#145: outside tests, a missing token must not make Logfire refuse to start.

    Logfire itself never sends under pytest, so the test checks the arguments
    configure_logfire passes rather than the resulting config.
    """
    import app.api.main as api_main

    calls = []
    monkeypatch.setattr(api_main, "is_testing", lambda: False)
    monkeypatch.setattr(api_main.settings, "logfire_token", None)
    monkeypatch.setattr(api_main.logfire, "configure", lambda **kw: calls.append(kw))
    configure_logfire()

    assert calls[0]["send_to_logfire"] is False
    assert "token" not in calls[0]
