"""Import-graph architecture contracts, mapped to ADRs.

Every rule is parametrized over the eleven modules and fails on any violation: all
modules are migrated, so nothing is report-only any more.
"""

import pytest

from tests.architecture.conftest import MODULES, RULE_KEYS


def _assert_clean(rule: str, module: str, violations: dict) -> None:
    offences = violations[rule][module]
    if offences:
        rendered = "\n".join(f"  - {o}" for o in offences)
        raise AssertionError(
            f"{_rule_display_name(rule)} violations in module '{module}':\n{rendered}"
        )


def _rule_display_name(rule: str) -> str:
    return {
        "module_order": "module-order (ADR-0003)",
        "facade_only": "facade-only (ADR-0003)",
        "layers": "in-module-layers (ADR-0002)",
        "get_session": "get_session (ADR-0001)",
    }[rule]


@pytest.mark.parametrize("module", MODULES)
def test_module_order(module, violations):
    _assert_clean("module_order", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_facade_only(module, violations):
    _assert_clean("facade_only", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_in_module_layers(module, violations):
    _assert_clean("layers", module, violations)


@pytest.mark.parametrize("module", MODULES)
def test_no_get_session(module, violations):
    _assert_clean("get_session", module, violations)


def test_module_list(import_graph):
    """The modules under app/modules must equal the enforced order list exactly."""
    found = {
        name[len("app.modules."):]
        for name in import_graph.find_children("app.modules")
    }
    assert found == set(MODULES), (
        "app/modules contents changed; update MODULES and the order in "
        "tests/architecture/conftest.py"
    )


def test_rule_result_keys_are_consistent(violations):
    """Every rule key has an entry for every module, so the summary table is complete."""
    for key in RULE_KEYS:
        for module in MODULES:
            assert isinstance(violations[key][module], list)