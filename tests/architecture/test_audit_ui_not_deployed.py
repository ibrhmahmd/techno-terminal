"""The audit demo UI (Streamlit) is not part of the API: building the app must never import it.

Streamlit is only an optional dependency (`uv sync --extra dashboard`) and
`app/modules/audit/ui/` is excluded from the deploy upload.
"""

import os
import subprocess
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

_SCRIPT = (
    "import sys\n"
    "from app.api.main import create_app\n"
    "create_app()\n"
    "bad = sorted(m for m in sys.modules if m.startswith('app.modules.audit.ui') or m == 'streamlit')\n"
    "print('\\n'.join(bad))\n"
    "sys.exit(1 if bad else 0)\n"
)


def test_create_app_does_not_import_the_demo_ui():
    env = {**os.environ, "SUPABASE_URL": "http://127.0.0.1:9", "TESTING": "true"}
    result = subprocess.run(
        [sys.executable, "-c", _SCRIPT], cwd=_ROOT, env=env, capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, result.stdout + result.stderr[-2000:]
