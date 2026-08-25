"""
app/observability/business_metrics.py
─────────────────────────────────────
Business KPI collector for Logfire.
Queries materialized views and emits metrics every collection interval.
"""
import asyncio
import logging
from contextlib import contextmanager
from typing import Any, Optional

import logfire
from sqlmodel import Session, text

from app.db.connection import get_engine

logger = logging.getLogger(__name__)


class BusinessMetricsCollector:
    """Collects business KPIs from database views and emits to Logfire."""

    # Single-value metrics (gauge/counter) — metric_name: SQL query returning one column
    SINGLE_METRICS = {
        # CRM / Enrollment
        "business_active_students": "SELECT active_students FROM v_bi_kpi_header",
        "business_waiting_students": "SELECT waiting_students FROM v_bi_kpi_header",
        "business_new_students_mtd": "SELECT new_students_this_month FROM v_bi_kpi_header",
        "business_active_groups": "SELECT active_groups FROM v_bi_kpi_header",

        # Finance / Revenue
        "business_revenue_mtd": "SELECT revenue_this_month FROM v_bi_kpi_header",
        "business_revenue_all_time": "SELECT revenue_all_time FROM v_bi_kpi_header",
        "business_avg_revenue_per_student": "SELECT avg_revenue_per_student FROM v_bi_kpi_header",
        "business_collection_rate_pct": "SELECT collection_rate_pct FROM v_bi_kpi_header",
        "business_outstanding_ar": "SELECT ar_total_owed FROM v_finance_summary",
        "business_high_risk_ar": "SELECT high_risk_total_owed FROM v_finance_summary",
        "business_active_ar_accounts": "SELECT ar_enrollment_count FROM v_finance_summary",
        "business_high_risk_accounts": "SELECT high_risk_count FROM v_finance_summary",
        "business_discounts_mtd": "SELECT discounts_this_month FROM v_finance_summary",
        "business_payroll_obligations": "SELECT active_contract_payroll FROM v_finance_summary",

        # Audit / Data Quality (aggregated by severity)
        "business_audit_critical_errors": (
            "SELECT COALESCE(SUM(anomaly_count), 0) FROM v_audit_summary WHERE severity = 'ERROR'"
        ),
        "business_audit_warnings": (
            "SELECT COALESCE(SUM(anomaly_count), 0) FROM v_audit_summary WHERE severity = 'WARNING'"
        ),
        "business_audit_info_items": (
            "SELECT COALESCE(SUM(anomaly_count), 0) FROM v_audit_summary WHERE severity = 'INFO'"
        ),

        # Operations
        "business_groups_over_capacity": "SELECT groups_over_capacity FROM v_bi_kpi_header",
        "business_idle_instructors": "SELECT idle_contract_instructors FROM v_bi_kpi_header",
        "business_demographics_completeness_pct": (
            "SELECT demographics_completeness_pct FROM v_bi_kpi_header"
        ),
    }

    # Per-scenario audit metrics (labeled metric)
    AUDIT_SCENARIOS_SQL = "SELECT code, anomaly_count FROM v_audit_summary"

    def __init__(self):
        self._engine = get_engine()
        self._gauges: dict[str, Any] = {}
        self._counters: dict[str, Any] = {}
        self._initialized = False

    def _init_metrics(self) -> None:
        """Create Logfire metric instruments (idempotent)."""
        if self._initialized:
            return

        # All metrics as gauges (current value snapshots)
        gauge_names = [
            "business_active_students",
            "business_waiting_students",
            "business_new_students_mtd",
            "business_active_groups",
            "business_revenue_mtd",
            "business_revenue_all_time",
            "business_avg_revenue_per_student",
            "business_collection_rate_pct",
            "business_outstanding_ar",
            "business_high_risk_ar",
            "business_active_ar_accounts",
            "business_high_risk_accounts",
            "business_discounts_mtd",
            "business_payroll_obligations",
            "business_audit_critical_errors",
            "business_audit_warnings",
            "business_audit_info_items",
            "business_groups_over_capacity",
            "business_idle_instructors",
            "business_demographics_completeness_pct",
        ]
        for name in gauge_names:
            self._gauges[name] = logfire.metric_gauge(name)

        # No separate counters needed - all metrics are gauge snapshots

        # Labeled gauge for audit scenarios
        self._audit_scenario_gauge = logfire.metric_gauge(
            "business_audit_scenario_count"
        )

        self._initialized = True

    @contextmanager
    def _session(self):
        """Context manager for database session."""
        with Session(self._engine, expire_on_commit=False) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise

    def _safe_scalar(self, session: Session, sql: str) -> Optional[float]:
        """Execute SQL and return scalar value, or None on failure."""
        try:
            result = session.exec(text(sql)).first()
            if result is None:
                return None
            # SQLModel's exec().first() returns a Row object, not a tuple
            # Row supports indexing and attribute access
            val = result[0] if hasattr(result, '__getitem__') else result
            return float(val) if val is not None else None
        except Exception as e:
            logger.warning(f"Metric query failed: {sql[:80]}... — {e}")
            return None

    def _safe_scalar_int(self, session: Session, sql: str) -> Optional[int]:
        """Execute SQL and return integer scalar value, or None on failure."""
        try:
            result = session.exec(text(sql)).first()
            if result is None:
                return None
            val = result[0] if hasattr(result, '__getitem__') else result
            return int(val) if val is not None else None
        except Exception as e:
            logger.warning(f"Metric query failed: {sql[:80]}... — {e}")
            return None

    def collect_once(self) -> None:
        """Run one collection cycle: query all metrics and emit to Logfire."""
        self._init_metrics()

        with self._session() as session:
            # Single-value metrics (all gauges)
            for metric_name, sql in self.SINGLE_METRICS.items():
                value = self._safe_scalar(session, sql)
                if value is not None:
                    self._gauges[metric_name].set(value)

            # Per-scenario audit metrics (labeled)
            try:
                rows = session.exec(text(self.AUDIT_SCENARIOS_SQL)).all()
                for row in rows:
                    code = row[0] if isinstance(row, tuple) else row.code
                    count = row[1] if isinstance(row, tuple) else row.anomaly_count
                    if count is not None:
                        self._audit_scenario_gauge.set(
                            float(count), {"scenario_code": str(code)}
                        )
            except Exception as e:
                logger.warning(f"Audit scenario metrics failed: {e}")

    async def run_forever(self, interval_seconds: int = 60) -> None:
        """Run collection loop forever with error handling and backoff."""
        logger.info(f"Starting business metrics collector (interval={interval_seconds}s)")
        consecutive_errors = 0
        max_consecutive_errors = 5

        while True:
            try:
                self.collect_once()
                consecutive_errors = 0
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Metrics collection failed (attempt {consecutive_errors}): {e}")
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({consecutive_errors}), stopping collector"
                    )
                    break
                # Exponential backoff
                await asyncio.sleep(min(interval_seconds * (2 ** (consecutive_errors - 1)), 300))
                continue

            try:
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                logger.info("Business metrics collector cancelled")
                break
            except Exception as e:
                logger.error(f"Sleep interrupted: {e}")
                break


# Singleton instance
_collector: Optional[BusinessMetricsCollector] = None


def get_collector() -> BusinessMetricsCollector:
    """Get or create the singleton collector instance."""
    global _collector
    if _collector is None:
        _collector = BusinessMetricsCollector()
    return _collector