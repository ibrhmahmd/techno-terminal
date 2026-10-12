from datetime import date

from app.db.uow import UnitOfWork
from app.modules.audit.constants import AUDIT_DATE_COLUMNS, SCENARIOS, SEVERITY_PRIORITY
from app.modules.audit.repositories import ViewRepository
from app.modules.audit.schemas import (
    ROW_DTO_BY_VIEW,
    AuditScenarioDTO,
    AuditScenarioRowsResult,
)
from app.shared.exceptions import NotFoundError

_SCENARIO_BY_CODE = {s["code"]: s for s in SCENARIOS}

# Each check's own sort (worst first, as the view defines it) plus its row key, so offset
# pagination is stable: it never repeats or skips a row.
_PAGE_ORDER = {
    "v_audit_zero_charge_enrollments": [("enrolled_at", "desc"), ("enrollment_id", "asc")],
    "v_audit_overpaid_enrollments": [("overpaid_by", "desc"), ("enrollment_id", "asc")],
    "v_audit_orphaned_payments": [("paid_at", "desc"), ("payment_id", "asc")],
    "v_audit_duplicate_enrollments": [("active_enrollment_count", "desc"), ("student_id", "asc"), ("group_id", "asc")],
    "v_audit_dead_group_enrollments": [("group_status", "asc"), ("group_name", "asc"), ("enrollment_id", "asc")],
    "v_audit_unrefunded_exits": [("net_collected", "desc"), ("enrollment_id", "asc")],
    "v_audit_level_mismatch": [("enrolled_at", "desc"), ("enrollment_id", "asc")],
    "v_audit_ghost_payments": [("student_deleted_at", "desc"), ("payment_id", "asc")],
    "v_audit_overdiscounted_enrollments": [("discount_pct", "desc"), ("enrollment_id", "asc")],
}


class AuditService:
    """The integrity checks A–I (ADR-0012: audit verifies). Read-only; never commits."""

    def __init__(self, uow: UnitOfWork) -> None:
        self._views = ViewRepository(uow.session)

    def list_scenarios(self) -> list[AuditScenarioDTO]:
        """Every check with its anomaly count, errors first, then warnings, then info."""
        summary = self._views.read("v_audit_summary", ["code", "anomaly_count"])
        counts = {code: count for code, count in summary.rows}
        scenarios = [
            AuditScenarioDTO(
                code=s["code"],
                label=s["label"],
                severity=s["severity"],
                anomaly_count=counts.get(s["code"], 0),
            )
            for s in SCENARIOS
        ]
        return sorted(scenarios, key=lambda s: (SEVERITY_PRIORITY[s.severity], s.code))

    def get_scenario_rows(
        self, code: str, since: date | None = None, skip: int = 0, limit: int = 50
    ) -> AuditScenarioRowsResult:
        """One page of a check's anomalies (worst first, as the view sorts them), optionally only those dated
        on or after ``since``."""
        scenario = _SCENARIO_BY_CODE.get(code.upper())
        if scenario is None:
            raise NotFoundError(f"Audit scenario {code} not found")
        view = scenario["view"]
        since_column = AUDIT_DATE_COLUMNS[view] if since else None
        page = self._views.read(
            view, order_by=_PAGE_ORDER[view], since_column=since_column, since=since, skip=skip, limit=limit
        )
        row_dto = ROW_DTO_BY_VIEW[view]
        return AuditScenarioRowsResult(
            code=scenario["code"],
            total=self._views.count(view, since_column, since),
            rows=[row_dto(**dict(zip(page.columns, row))) for row in page.rows],
        )
