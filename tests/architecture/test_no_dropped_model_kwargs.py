"""No call passes a keyword argument that its Pydantic model does not define (#151).

Pydantic ignores unknown keyword arguments by default, so a typo or a field
that was never added to the schema is silently dropped (#70, #149, #151).
This walks every ``Model(...)`` call under ``app/`` (tests excluded), resolves
``Model`` through the calling module's globals and fails on any keyword the
model neither defines as a field nor as an alias.
"""

import ast
import importlib
import os
from pathlib import Path

from pydantic import BaseModel

os.environ.setdefault("SUPABASE_URL", "http://127.0.0.1:9")

_ROOT = Path(__file__).resolve().parents[2]
_SKIP_PARTS = {"tests", "ui"}


def _accepted_names(model: type[BaseModel]) -> set[str] | None:
    """Field names and aliases the model accepts; None when it allows extras."""
    if model.model_config.get("extra") == "allow":
        return None
    names = set(model.model_fields)
    for field in model.model_fields.values():
        for alias in (field.alias, field.validation_alias):
            if isinstance(alias, str):
                names.add(alias)
    return names


def _dropped_kwargs() -> list[str]:
    found = []
    for path in sorted((_ROOT / "app").rglob("*.py")):
        rel = path.relative_to(_ROOT)
        if _SKIP_PARTS & set(rel.parts):
            continue
        module = importlib.import_module(".".join(rel.with_suffix("").parts).removesuffix(".__init__"))
        for node in ast.walk(ast.parse(path.read_text())):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                continue
            model = getattr(module, node.func.id, None)
            if not (isinstance(model, type) and issubclass(model, BaseModel)):
                continue
            accepted = _accepted_names(model)
            if accepted is None:
                continue
            for kw in node.keywords:
                # Leading-underscore keywords are init options (e.g. BaseSettings(_env_file=...)).
                if kw.arg is not None and not kw.arg.startswith("_") and kw.arg not in accepted:
                    found.append(f"{rel}:{node.lineno} {model.__name__}({kw.arg}=...)")
    return found


def test_no_model_call_passes_an_unknown_keyword():
    dropped = _dropped_kwargs()
    assert not dropped, "Keyword arguments the model silently drops:\n" + "\n".join(dropped)
