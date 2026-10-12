"""
Unit tests for the settings env-file selection logic in app/core/config.py.

Pure selection only — no database or network access.
"""
import os
from urllib.parse import urlparse

import pytest

from app.core.config import select_env_file


def test_non_testing_always_uses_dotenv(tmp_path):
    (tmp_path / ".env.test.local").write_text("")
    assert select_env_file(False, {"TEST_ENV_FILE": "/tmp/x.env"}, str(tmp_path)) == ".env"


def test_testing_explicit_env_file_wins(tmp_path):
    explicit = str(tmp_path / "custom.env")
    result = select_env_file(True, {"TEST_ENV_FILE": explicit}, str(tmp_path))
    assert result == explicit


def test_testing_prefers_local_when_present(tmp_path):
    local = tmp_path / ".env.test.local"
    local.write_text("DATABASE_URL=postgresql://postgres:pw@127.0.0.1:55432/techno_test\n")
    result = select_env_file(True, {}, str(tmp_path))
    assert result == str(local)
    assert os.path.isabs(result)


def test_testing_falls_back_to_env_test(tmp_path):
    result = select_env_file(True, {}, str(tmp_path))
    assert result == str(tmp_path / ".env.test")


def test_effective_database_url_is_local_under_local_env():
    """Proof that pytest talks to the disposable localhost DB, not the cloud."""
    from app.core.config import _env_file, settings

    if not os.path.exists(os.path.join(os.path.dirname(_env_file), ".env.test.local")):
        pytest.skip("no .env.test.local — local gate not active")

    parsed = urlparse(settings.database_url)
    assert parsed.hostname in {"127.0.0.1", "localhost"}
    assert parsed.port == 55432
