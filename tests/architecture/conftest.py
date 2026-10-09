"""Fixtures and helpers for the architecture contract tests.

The import graph is built once per session with grimp. Each rule is computed
once and stored in the module-level ``RULE_RESULTS`` dict so that
``pytest_terminal_summary`` can render the per-module / per-rule violation
table at the end of every run.
"""

import ast
import os

import pytest
from grimp import build_graph

# Module order, TOP to BOTTOM (a module may import only modules BELOW it).
# Source of truth for the rule tests. A new module must be added here AND in
# the order below, otherwise test_module_rules::test_module_list fails.
MODULES = [
    "analytics",
    "notifications",
    "tasks",
    "finance",
    "competitions",
    "attendance",
    "enrollments",
    "academics",
    "crm",
    "hr",
    "auth",
]

# Lower index = higher in the order.
ORDER = {name: i for i, name in enumerate(MODULES)}

# Display names are owned by the pytest_terminal_summary renderer below.
RULE_KEYS = ["module_order", "facade_only", "layers", "get_session"]

_PREFIX = "app.modules."
_LAYERS = ("api", "services", "repositories", "schemas", "models")
_GET_SESSION_ALLOW = ("app/modules/notifications/adapters",)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_APP_ROOT = os.path.join(_PROJECT_ROOT, "app")


def _module_of(dotted: str) -> str | None:
    """Top-level module name ("crm") for a dotted path, or None if not under app.modules."""
    if not dotted.startswith(_PREFIX):
        return None
    return dotted[len(_PREFIX):].split(".", 1)[0]


def _relpath(module: str) -> str:
    """File path (relative to repo root) for a grimp module name."""
    path = "app/" + module[len("app."):].replace(".", "/")
    if os.path.isdir(os.path.join(_PROJECT_ROOT, path)):
        return path + "/__init__.py"
    return path + ".py"


def _is_facade_import(imported: str, module: str) -> bool:
    """True when the import touches the facade (``app.modules.<module>``)
    or the shared models layer (``app.modules.<module>.models[. ...]``)."""
    prefix = f"{_PREFIX}{module}"
    if not imported.startswith(prefix):
        return False
    suffix = imported[len(prefix):]
    return suffix == "" or suffix.startswith(".models")


def _is_models_import(imported: str, module: str) -> bool:
    """True when the import touches only the models layer
    (``app.modules.<module>.models[. ...]``) — ADR-0004's read exemption."""
    prefix = f"{_PREFIX}{module}.models"
    return imported == prefix or imported.startswith(prefix + ".")


def _violation(importer: str, imported: str, file: str, lineno: int | None) -> str:
    if lineno is None:
        return f"{importer} -> {imported} ({file})"
    return f"{importer} -> {imported} ({file}:{lineno})"


def _cross_module_imports(graph):
    """Yield (importer, imported, importer_module, imported_module, file, lineno)
    for every direct cross-module import under app.modules."""
    for importer in sorted(graph.modules):
        x = _module_of(importer)
        if x is None:
            continue
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            y = _module_of(imported)
            if y is None or y == x:
                continue
            details = graph.get_import_details(importer=importer, imported=imported)
            if not details:
                yield importer, imported, x, y, _relpath(importer), None
            else:
                for d in sorted(details, key=lambda d: d["line_number"]):
                    yield importer, imported, x, y, _relpath(importer), d["line_number"]


def _module_order_violations(graph) -> dict[str, list[str]]:
    """ADR-0003: a module may import only modules below it, except models."""
    result: dict[str, list[str]] = {}
    for importer, imported, x, y, file, lineno in _cross_module_imports(graph):
        if ORDER[y] >= ORDER[x]:
            continue
        if _is_models_import(imported, y):
            continue  # ADR-0004: any model may be read from anywhere.
        result.setdefault(x, []).append(_violation(importer, imported, file, lineno))
    return result


def _facade_only_violations(graph) -> dict[str, list[str]]:
    """ADR-0003: cross-module imports must touch the facade or models only."""
    result: dict[str, list[str]] = {}
    for importer, imported, x, y, file, lineno in _cross_module_imports(graph):
        if _is_facade_import(imported, y):
            continue
        result.setdefault(x, []).append(_violation(importer, imported, file, lineno))
    return result


def _layers_violations(graph) -> dict[str, list[str]]:
    """ADR-0002: within a module, layers point downward only."""
    result: dict[str, list[str]] = {}
    for importer in sorted(graph.modules):
        x = _module_of(importer)
        if x is None:
            continue
        importer_layer = _layer_of(importer, x)
        if importer_layer is None:
            continue
        for imported in sorted(graph.find_modules_directly_imported_by(importer)):
            y = _module_of(imported)
            if y != x:
                continue
            imported_layer = _layer_of(imported, x)
            if imported_layer is None:
                continue
            if not _forbidden_layer_move(importer_layer, imported_layer):
                continue
            details = graph.get_import_details(importer=importer, imported=imported)
            if not details:
                result.setdefault(x, []).append(
                    _violation(importer, imported, _relpath(importer), None)
                )
            else:
                for d in sorted(details, key=lambda d: d["line_number"]):
                    result.setdefault(x, []).append(
                        _violation(importer, imported, _relpath(importer), d["line_number"])
                    )
    return result


def _layer_of(module: str, top: str) -> str | None:
    """First layer segment (api/services/repositories/schemas/models) after
    ``app.modules.<top>.``, or None if the module has no layer segment."""
    after = module[len(_PREFIX) + len(top):]
    for segment in after.split("."):
        if segment in _LAYERS:
            return segment
    return None


def _forbidden_layer_move(importer_layer: str, imported_layer: str) -> bool:
    if importer_layer == "services" and imported_layer == "api":
        return True
    if importer_layer == "repositories" and imported_layer in ("services", "api"):
        return True
    if importer_layer in ("schemas", "models") and imported_layer in (
        "services",
        "repositories",
        "api",
    ):
        return True
    return False


def _get_session_violations() -> dict[str, list[str]]:
    """ADR-0001: no get_session() under app/modules, except notifications/adapters."""
    result: dict[str, list[str]] = {}
    for root, dirs, files in os.walk(_APP_ROOT):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for name in files:
            if not name.endswith(".py"):
                continue
            path = os.path.join(root, name)
            rel = os.path.relpath(path, _PROJECT_ROOT)
            if _is_allow_listed(rel):
                continue
            module = _file_to_module(rel)
            x = _module_of(module)
            if x is None:
                continue
            try:
                tree = ast.parse(open(path, encoding="utf-8").read())
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                lineno = _get_session_line(node)
                if lineno is not None:
                    result.setdefault(x, []).append(f"{rel}:{lineno}")
    return result


def _is_allow_listed(rel: str) -> bool:
    for allowed in _GET_SESSION_ALLOW:
        if rel == allowed or rel.startswith(allowed + os.sep):
            return True
    return False


def _file_to_module(rel: str) -> str:
    dotted = rel[:-3].replace(os.sep, ".")
    if dotted.endswith(".__init__"):
        dotted = dotted[: -len(".__init__")]
    return dotted


def _get_session_line(node) -> int | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "get_session":
        return node.lineno
    if isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name == "get_session":
                return node.lineno
    if isinstance(node, ast.Import):
        for alias in node.names:
            if alias.name == "get_session" or alias.name.endswith(".get_session"):
                return node.lineno
    return None


# Populated once by the `violations` fixture; read by pytest_terminal_summary.
RULE_RESULTS: dict[str, dict[str, list[str]]] = {
    key: {module: [] for module in MODULES} for key in RULE_KEYS
}
_COMPUTED = False


@pytest.fixture(scope="session")
def import_graph():
    """Session-scoped grimp import graph for the app package."""
    return build_graph("app", cache_dir=None)


@pytest.fixture(scope="session")
def violations(import_graph):
    """Rule -> module -> list of violation strings, computed once per session."""
    global _COMPUTED
    for key, violations_for_rule in (
        ("module_order", _module_order_violations(import_graph)),
        ("facade_only", _facade_only_violations(import_graph)),
        ("layers", _layers_violations(import_graph)),
        ("get_session", _get_session_violations()),
    ):
        for module, lines in violations_for_rule.items():
            RULE_RESULTS[key][module] = lines
    _COMPUTED = True
    return RULE_RESULTS


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Render the per-module / per-rule violation table (report-only counts)."""
    if not _COMPUTED:
        return
    tw = terminalreporter
    header = (
        f"{'module':<13}{'module order':>14}{'facade only':>14}"
        f"{'layers':>16}{'get_session':>14}{'total':>8}"
    )
    tw.write_line("")
    tw.write_line("architecture contracts — violations per module (report-only; "
                  "module fails only when in ENFORCED_MODULES)")
    tw.write_line(header)
    tw.write_line("-" * len(header))
    totals = {key: 0 for key in RULE_KEYS}
    grand_total = 0
    for module in MODULES:
        row_total = 0
        cells = []
        for key in RULE_KEYS:
            count = len(RULE_RESULTS[key][module])
            totals[key] += count
            row_total += count
            cells.append(count)
        grand_total += row_total
        tw.write_line(
            f"{module:<13}{cells[0]:>14}{cells[1]:>14}{cells[2]:>16}{cells[3]:>14}{row_total:>8}"
        )
    tw.write_line("-" * len(header))
    tw.write_line(
        f"{'total':<13}{totals['module_order']:>14}{totals['facade_only']:>14}"
        f"{totals['layers']:>16}{totals['get_session']:>14}{grand_total:>8}"
    )