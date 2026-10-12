"""Tests live with the code they test (#109).

Every ``test_*.py`` sits in a ``tests`` package under ``app/`` (next to its
module, or next to ``app/db``, ``app/api``...), except the repo-wide contract
tests in ``tests/architecture``.
"""

import os

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".specify", ".opencode", ".scratch", "specs"}


def _test_files():
    for root, dirs, files in os.walk(_ROOT):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith(".")]
        for name in files:
            if name.startswith("test_") and name.endswith(".py"):
                yield os.path.relpath(os.path.join(root, name), _ROOT)


def _allowed(rel: str) -> bool:
    parts = rel.split(os.sep)
    if parts[:2] == ["tests", "architecture"]:
        return True
    return parts[0] == "app" and "tests" in parts[:-1]


def test_every_test_file_lives_in_a_tests_package():
    misplaced = sorted(rel for rel in _test_files() if not _allowed(rel))
    assert not misplaced, (
        "Test files must live in app/**/tests/ (or tests/architecture/):\n  "
        + "\n  ".join(misplaced)
    )
