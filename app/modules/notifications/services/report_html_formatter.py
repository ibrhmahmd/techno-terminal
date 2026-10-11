"""
app/modules/notifications/services/report_html_formatter.py
─────────────────────────────────────────────────────────────
Pure HTML table formatting functions for report notifications.

These functions take typed DTO lists and return HTML strings for email templates.
Zero business logic — presentation only.
"""

from typing import List



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


