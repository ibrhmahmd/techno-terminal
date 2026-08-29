"""
app/modules/notifications/services/report_html_formatter.py
─────────────────────────────────────────────────────────────
Pure HTML table formatting functions for report notifications.

These functions take typed DTO lists and return HTML strings for email templates.
Zero business logic — presentation only.
"""

from typing import List, Optional

from app.modules.notifications.schemas.report_dto import (
    TopGroupRevenueItem,
    CourseRevenueItem,
    CourseEnrollmentItem,
    InstructorSessionItem,
    CoursePerformanceItem,
    PaymentTypeRevenueItem,
)


def _row_html(cells: List[str], row_class: str = "", is_header: bool = False) -> str:
    """Build a table row with optional class and header cells."""
    tag = "th" if is_header else "td"
    style = 'style="padding:4px 8px;border-bottom:1px solid #e2e8f0;"'
    if is_header:
        style += ' background:#f8f9ff;font-weight:600;'
    cells_html = "".join(f"<{tag} {style}>{cell}</{tag}>" for cell in cells)
    cls = f' class="{row_class}"' if row_class else ""
    return f"<tr{cls}>{cells_html}</tr>"


def _table_html(rows: List[str], width: str = "100%", font_size: str = "12px") -> str:
    """Wrap rows in a styled table."""
    return (
        f'<table style="width:{width};font-size:{font_size};border-collapse:collapse;">'
        f"{''.join(rows)}</table>"
    )


def _empty_msg_html(msg: str, color: str = "#64748b", bg: str = "#ffffff") -> str:
    """Return a centered empty-state message."""
    return (
        f'<p style="font-size:12px;color:{color};text-align:center;'
        f'padding:16px;background:{bg};margin:0;">{msg}</p>'
    )


def format_top_groups_table(
    items: List[TopGroupRevenueItem], empty_msg: str = "No revenue generated this period."
) -> str:
    """Format top groups revenue as HTML table."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Group", "Revenue (EGP)"], is_header=True)
    rows = [
        _row_html([item.group_name, f"{item.revenue:,.2f}"])
        for item in items
    ]
    return _table_html([header] + rows)


def format_course_revenue_table(
    items: List[CourseRevenueItem], empty_msg: str = "No revenue generated this period."
) -> str:
    """Format course revenue as HTML table."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Course", "Revenue (EGP)"], is_header=True)
    rows = [
        _row_html([item.course_name, f"{item.revenue:,.2f}"])
        for item in items
    ]
    return _table_html([header] + rows)


def format_top_courses_table(
    items: List[CourseEnrollmentItem], empty_msg: str = "No new enrollments this period."
) -> str:
    """Format top courses by enrollment count as HTML table."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Course", "New Enrollments"], is_header=True)
    rows = [
        _row_html([item.course_name, str(item.enrollment_count)])
        for item in items
    ]
    return _table_html([header] + rows)


def format_revenue_breakdown_table(
    items: List[PaymentTypeRevenueItem], empty_msg: str = "No revenue generated this period."
) -> str:
    """Format revenue breakdown by payment type as HTML table."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Type", "Revenue (EGP)"], is_header=True)
    rows = [
        _row_html([item.payment_type.capitalize(), f"{item.revenue:,.2f}"])
        for item in items
    ]
    return _table_html([header] + rows)


def format_top_instructors_table_weekly(
    items: List[InstructorSessionItem], empty_msg: str = "No sessions held this period."
) -> str:
    """Format top instructors for weekly report (sessions only)."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Instructor", "Sessions Held"], is_header=True)
    rows = [
        _row_html([item.instructor_name, str(item.session_count)])
        for item in items
    ]
    return _table_html([header] + rows)


def format_top_instructors_table_monthly(
    items: List[InstructorSessionItem], empty_msg: str = "No sessions held this period."
) -> str:
    """Format top instructors for monthly report (sessions + students taught)."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(["Instructor", "Sessions Held", "Students Taught"], is_header=True)
    rows = [
        _row_html([
            item.instructor_name,
            str(item.session_count),
            str(item.students_taught or 0)
        ])
        for item in items
    ]
    return _table_html([header] + rows)


def format_course_performance_table(
    items: List[CoursePerformanceItem], empty_msg: str = "No course activity this period."
) -> str:
    """Format course performance matrix as HTML table."""
    if not items:
        return _empty_msg_html(empty_msg)
    header = _row_html(
        ["Course", "Rev (EGP)", "New", "Drops"],
        is_header=True
    )
    rows = [
        _row_html([
            item.course_name,
            f"{item.revenue:,.2f}",
            str(item.enrollments_count),
            str(item.drops_count)
        ])
        for item in items
    ]
    return _table_html([header] + rows)