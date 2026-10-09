"""OpenAPI specification snapshot test.

The spec is generated from the fully-built FastAPI app, so any API shape
change shows up here. Regenerate deliberately (only for a ticket that names
an API change) with UPDATE_OPENAPI_SNAPSHOT=1.
"""

import difflib
import json
import os
from pathlib import Path

import pytest

from app.api.main import create_app

SNAPSHOT_PATH = Path(__file__).resolve().parents[1] / "snapshots" / "openapi.json"
_DIFF_PREVIEW_LINES = 80


def current_spec() -> str:
    spec = create_app().openapi()
    return json.dumps(spec, indent=2, sort_keys=True) + "\n"


def test_openapi_snapshot():
    if os.environ.get("UPDATE_OPENAPI_SNAPSHOT") == "1":
        SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
        SNAPSHOT_PATH.write_text(current_spec(), encoding="utf-8")
        return

    if not SNAPSHOT_PATH.exists():
        pytest.fail(
            "tests/snapshots/openapi.json is missing; regenerate it with "
            "UPDATE_OPENAPI_SNAPSHOT=1 pytest tests/architecture/test_openapi_snapshot.py"
        )

    expected = SNAPSHOT_PATH.read_text(encoding="utf-8")
    actual = current_spec()
    if actual == expected:
        return

    diff = list(
        difflib.unified_diff(
            expected.splitlines(),
            actual.splitlines(),
            fromfile="tests/snapshots/openapi.json",
            tofile="<generated>",
            lineterm="",
        )
    )
    preview = diff[:_DIFF_PREVIEW_LINES]
    message = "\n".join(preview)
    remaining = len(diff) - len(preview)
    if remaining > 0:
        message += f"\n... and {remaining} more differing lines"
    pytest.fail(
        "OpenAPI spec changed. If this change is intentional and ticketed, "
        f"regenerate with UPDATE_OPENAPI_SNAPSHOT=1.\n\n{message}"
    )