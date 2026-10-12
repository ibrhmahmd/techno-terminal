"""AuditViewService: every catalogued view is readable, and only catalogued names reach SQL."""

from datetime import date

import pytest

from app.modules.audit import AuditViewService, ViewRows
from app.modules.audit.constants import ALLOWED_VIEWS, AUDIT_DATE_COLUMNS
from app.shared.exceptions import ValidationError


@pytest.mark.parametrize("view", sorted(ALLOWED_VIEWS))
def test_every_catalogued_view_is_readable(uow, view):
    result = AuditViewService(uow).read_view(view)
    assert isinstance(result, ViewRows)
    assert result.view == view
    assert result.columns
    assert all(len(row) == len(result.columns) for row in result.rows)


def test_selected_columns_come_back_in_order(uow):
    result = AuditViewService(uow).read_view(
        "v_audit_summary", ["code", "anomaly_count"], order_by="code"
    )
    assert result.columns == ["code", "anomaly_count"]
    codes = [row[0] for row in result.rows]
    assert codes == sorted(codes)


@pytest.mark.parametrize(
    "view", sorted(v for v, col in AUDIT_DATE_COLUMNS.items() if col)
)
def test_since_filter_applies_to_dated_audit_views(uow, view):
    result = AuditViewService(uow).read_view(view, since=date(2100, 1, 1))
    assert result.rows == []


def test_since_is_ignored_for_views_without_a_date_column(uow):
    svc = AuditViewService(uow)
    assert (
        svc.read_view("v_audit_overpaid_enrollments", since=date(2100, 1, 1)).rows
        == svc.read_view("v_audit_overpaid_enrollments").rows
    )


@pytest.mark.parametrize("view", ["students", "v_unknown", 'v_audit_summary"; DROP TABLE students; --'])
def test_unknown_view_is_rejected(uow, view):
    with pytest.raises(ValidationError):
        AuditViewService(uow).read_view(view)


@pytest.mark.parametrize("column", ['code"; --', "Code", "1code", "code name"])
def test_invalid_column_name_is_rejected(uow, column):
    with pytest.raises(ValidationError):
        AuditViewService(uow).read_view("v_audit_summary", [column])
    with pytest.raises(ValidationError):
        AuditViewService(uow).read_view("v_audit_summary", order_by=column)


def test_every_check_has_a_page_order_that_exists_in_its_view(uow):
    from app.modules.audit.constants import SCENARIOS
    from app.modules.audit.services.audit_service import _PAGE_ORDER

    for scenario in SCENARIOS:
        columns = AuditViewService(uow).read_view(scenario["view"]).columns
        assert {c for c, _ in _PAGE_ORDER[scenario["view"]]} <= set(columns)
