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