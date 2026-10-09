"""Ticket 06: time send_{daily,weekly,monthly}_report phases against the testing DB.

SMTP is stubbed (GmailEmailDispatcher.send), and _dispatch is replaced by a
render-only timer, so no emails go out and no notification_logs rows are written.
"""
import asyncio, os, statistics, sys, time
from collections import defaultdict
from datetime import date

sys.path.insert(0, "/home/ibrahim/Desktop/techno-terminal")
os.chdir("/home/ibrahim/Desktop/techno-terminal")

import app.api.main  # noqa: F401  (same import order as the server; avoids a circular import)
from app.core.config import settings
assert "127.0.0.1" in settings.database_url or "localhost" in settings.database_url, "refusing to run against a non-local database"
print("DB project:", settings.database_url.split("@")[0].split(".")[-1].split(":")[0])

from app.db.connection import get_session
from app.modules.notifications.dispatchers.email_dispatcher import GmailEmailDispatcher
from app.modules.notifications.repositories.notification_repository import NotificationRepository
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.services import report_notifications as rn
from app.modules.notifications.services.base_notification_service import BaseNotificationService
import app.modules.notifications.pdf.daily_report_pdf as pdfmod

timings = defaultdict(list)
current = {}

def timed(name, fn, is_async=False):
    if is_async:
        async def w(*a, **k):
            t = time.perf_counter()
            try: return await fn(*a, **k)
            finally: current[name] = current.get(name, 0) + time.perf_counter() - t
    else:
        def w(*a, **k):
            t = time.perf_counter()
            try: return fn(*a, **k)
            finally: current[name] = current.get(name, 0) + time.perf_counter() - t
    return w

async def fake_send(self, *a, **k):
    raise AssertionError("SMTP must not be called")
GmailEmailDispatcher.send = fake_send

recipients_seen = {}
async def render_only_dispatch(self, template, channel, rtype, rid, contact, variables, attachments=None):
    t = time.perf_counter()
    body = self._render_template(template, variables)
    current["render"] = current.get("render", 0) + time.perf_counter() - t
    current["recipients"] = current.get("recipients", 0) + 1
    current["body_kb"] = len(body) / 1024
    if attachments:
        current["pdf_kb"] = len(attachments[0][1]) / 1024

S = rn.ReportNotificationService
S._dispatch = render_only_dispatch
# Testing DB has no report templates: load prod's rows read-only, inject in memory.
import psycopg2
from app.modules.notifications.models.notification_template import NotificationTemplate
_pc = psycopg2.connect(os.environ["PROD_URL"]); _pc.set_session(readonly=True); _cur = _pc.cursor()
_cur.execute("show transaction_read_only"); assert _cur.fetchone()[0] == "on"
_cur.execute("select * from notification_templates where name in ('daily_report','weekly_report','monthly_report')")
_cols = [d[0] for d in _cur.description]
PROD_TEMPLATES = {r[_cols.index("name")]: NotificationTemplate(**dict(zip(_cols, r))) for r in _cur.fetchall()}
_pc.rollback(); _pc.close()
print("injected templates:", {k: (v.id, v.is_active) for k, v in PROD_TEMPLATES.items()})
S._get_template_by_name = timed("template", lambda self, name: PROD_TEMPLATES.get(name))
S._resolve_notification_recipients = timed("recipients_lookup", S._resolve_notification_recipients)
S._fetch_daily_aggregates = timed("aggregates", S._fetch_daily_aggregates)
S._fetch_weekly_aggregates = timed("aggregates", S._fetch_weekly_aggregates)
S._fetch_monthly_aggregates = timed("aggregates", S._fetch_monthly_aggregates)
S._build_variables = timed("build_vars", S._build_variables)
pdfmod.generate_daily_report_pdf = timed("pdf", pdfmod.generate_daily_report_pdf)

CASES = [
    ("daily", "send_daily_report", date(2026, 7, 25)),
    ("weekly", "send_weekly_report", date(2026, 7, 26)),
    ("monthly", "send_monthly_report", date(2026, 7, 31)),
]
RUNS = 4

async def main():
    for label, method, d in CASES:
        for i in range(RUNS):
            current.clear()
            with get_session() as session:
                svc = NotificationService(NotificationRepository(session))
                t = time.perf_counter()
                await getattr(svc, method)(target_date=d)
                total = time.perf_counter() - t
            current["total"] = total
            for k, v in current.items():
                timings[(label, k)].append(v)
            print(f"{label} run {i+1}: " + ", ".join(f"{k}={v:.2f}" for k, v in current.items()))
    print("\n=== summary (seconds; run 1 = cold, median of warm runs 2..N) ===")
    for label, _, _ in CASES:
        keys = sorted({k for (l, k) in timings if l == label})
        row = []
        for k in keys:
            v = timings[(label, k)]
            row.append(f"{k}: cold={v[0]:.2f} warm={statistics.median(v[1:]):.2f} max={max(v):.2f}")
        print(f"{label}:\n  " + "\n  ".join(row))

asyncio.run(main())
