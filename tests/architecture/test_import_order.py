"""Every module facade must be importable first, in a fresh interpreter.

Lower modules read higher modules' models (ADR-0004), which runs the higher module's
``__init__``. If that facade eagerly imported its services, importing a lower module
first could hit a half-initialised package. Facades whose models are read from below
therefore load their services lazily; this test guards that nobody breaks it.
"""

import os
import subprocess
import sys

import pytest

from tests.architecture.conftest import MODULES

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_standalone(module):
    env = {**os.environ, "SUPABASE_URL": "http://127.0.0.1:9", "TESTING": "true"}
    result = subprocess.run(
        [sys.executable, "-c", f"import app.modules.{module}"],
        cwd=_ROOT, env=env, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
