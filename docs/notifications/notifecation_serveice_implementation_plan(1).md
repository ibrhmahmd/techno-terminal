# Notification Service — Full Implementation Plan

## Overview

A new `notifications` domain module following the **Finance-Pattern N-Tier SOLID architecture** exactly. The service handles two channels (**Twilio WhatsApp** + **Gmail SMTP via smtplib**) with zero added dependencies beyond `twilio` (1 package). All external calls are non-blocking via FastAPI `BackgroundTasks`. Scheduled reports use a self-contained `asyncio` background task started at app `lifespan`.

---

## User Review Required

> [!IMPORTANT]
> **New Environment Variables Required.** After approval, you will need to add the following to your `.env` file before the code can run:
> - `TWILIO_ACCOUNT_SID` — From your Twilio Console
> - `TWILIO_AUTH_TOKEN` — From your Twilio Console
> - `TWILIO_WHATSAPP_FROM` — Your Twilio WhatsApp sender (e.g. `whatsapp:+14155238886` for sandbox)
> - `GMAIL_SENDER_ADDRESS` — Your business Gmail address
> - `GMAIL_APP_PASSWORD` — Gmail "App Password" (not your account password, generated in Google Account Security settings)
> - `REPORT_RECIPIENT_EMAIL` — Admin email for scheduled reports (can be same as sender initially)

> [!WARNING]
> **Twilio WhatsApp Sandbox vs Production.** Twilio provides a **free sandbox** for instant testing — no Meta approval needed. For production sends to real parents, Meta template approval is required (takes ~24–48 hrs). The architecture supports both; only the `TWILIO_WHATSAPP_FROM` number changes.

---

## Architecture Map

```
app/
├── modules/
│   └── notifications/               ← NEW domain module
│       ├── __init__.py
│       ├── models/
│       │   ├── notification_log.py      # DB: audit log of every send attempt
│       │   ├── notification_template.py # DB: message templates
│       │   └── notification_subscriber.py # DB: report recipients (employees)
│       ├── schemas/
│       │   ├── notification_dto.py      # NotificationLogDTO (response)
│       │   ├── template_dto.py          # TemplateDTO, CreateTemplateRequest
│       │   └── send_request.py          # SendWhatsAppRequest, SendEmailRequest, BulkSendRequest
│       ├── repositories/
│       │   └── notification_repository.py
│       ├── dispatchers/
│       │   ├── i_dispatcher.py          # Protocol (abstract interface)
│       │   ├── whatsapp_dispatcher.py   # Twilio implementation
│       │   └── email_dispatcher.py      # Gmail SMTP implementation
│       ├── services/
│       │   ├── notification_service.py  # Main orchestrator
│       │   └── report_scheduler.py      # asyncio background task
│       └── interfaces/
│           ├── __init__.py
│           └── i_notification_repository.py
│
└── api/
    └── routers/
        └── notifications/               ← NEW router group
            ├── __init__.py
            ├── notifications_router.py  # Send, logs, absence trigger
            ├── templates_router.py      # Template CRUD
            └── bulk_router.py           # Bulk marketing sends
```

---

## Phase 1 — Database Models & Migration

### [NEW] `notification_template.py`

```python
class NotificationTemplate(SQLModel, table=True):
    __tablename__ = "notification_templates"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True)        # e.g. "absence_alert", "payment_receipt"
    channel: str                           # "WHATSAPP" | "EMAIL"
    subject: str | None = None            # Email only; ignored for WhatsApp
    body: str                             # Body with {{variable}} placeholders
    variables: list[str] = Field(...)     # ARRAY(String) — e.g. ["student_name", "amount"]
    is_standard: bool = Field(default=False)   # Standard templates cannot be deleted
    is_active: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime | None = None
```

### [NEW] `notification_log.py`

```python
class NotificationLog(SQLModel, table=True):
    __tablename__ = "notification_logs"
    id: int | None = Field(default=None, primary_key=True)
    template_id: int | None = Field(foreign_key="notification_templates.id")
    channel: str                     # "WHATSAPP" | "EMAIL"
    recipient_type: str              # "PARENT" | "EMPLOYEE"
    recipient_id: int                # PK of parent or employee
    recipient_contact: str           # Phone/email captured at send time
    subject: str | None = None
    body: str                        # Fully rendered body
    status: str                      # "PENDING" | "SENT" | "FAILED"
    error_message: str | None = None
    sent_at: datetime | None = None
    created_at: datetime
    # campaign_id: int | None = None  ← Reserved for Phase 2 (Campaigns)
```

### [NEW] `notification_subscriber.py`

```python
class NotificationSubscriber(SQLModel, table=True):
    __tablename__ = "notification_subscribers"
    id: int | None = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id")
    report_type: str   # "DAILY" | "WEEKLY" | "MONTHLY" | "ALL"
    channel: str       # "EMAIL" | "WHATSAPP"
    is_active: bool = Field(default=True)
```

### [NEW] Migration file (SQL)

- Create all 3 tables with proper indexes
- **Seed 7 standard templates** (see below)

### Standard Seed Templates

| Name | Channel | Variables |
|---|---|---|
| `absence_alert` | WHATSAPP | parent_name, student_name, session_name, session_date |
| `enrollment_confirmation` | WHATSAPP | parent_name, student_name, group_name, course_name |
| `payment_receipt` | WHATSAPP | parent_name, student_name, amount, receipt_number |
| `daily_report` | EMAIL | date, total_revenue, new_enrollments, sessions_held, absent_count |
| `weekly_report` | EMAIL | week_start, week_end, total_revenue, new_students, attendance_rate |
| `monthly_report` | EMAIL | month, total_revenue, new_enrollments, active_students |
| `bulk_marketing` | WHATSAPP | custom_message *(admin fills this freely)* |

---

## Phase 2 — Abstract Dispatcher Interface

### [NEW] `dispatchers/i_dispatcher.py`

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class IMessageDispatcher(Protocol):
    async def send(
        self,
        recipient: str,       # phone number or email address
        body: str,
        subject: str | None = None,   # email only
    ) -> tuple[bool, str | None]:
        """
        Returns (success: bool, error_message: str | None).
        Never raises — errors are returned, not thrown.
        """
        ...
```

This Protocol ensures both dispatchers are **swappable** without touching the service layer. If you migrate from Twilio to Meta direct or from Gmail to SendGrid, only the dispatcher file changes.

---

## Phase 3 — Concrete Dispatchers

### [NEW] `dispatchers/whatsapp_dispatcher.py` (Twilio)

```python
from twilio.rest import Client
from app.core.config import settings

class TwilioWhatsAppDispatcher:
    def __init__(self):
        self._client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self._from = settings.TWILIO_WHATSAPP_FROM  # "whatsapp:+14155238886"

    async def send(self, recipient: str, body: str, **_) -> tuple[bool, str | None]:
        try:
            msg = self._client.messages.create(
                body=body,
                from_=self._from,
                to=f"whatsapp:{recipient}",
            )
            return (True, None) if msg.sid else (False, "No SID returned")
        except Exception as e:
            return False, str(e)
```

### [NEW] `dispatchers/email_dispatcher.py` (Gmail SMTP)

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from app.core.config import settings

class GmailEmailDispatcher:
    """
    Zero-dependency email dispatcher using stdlib smtplib.
    Architecture is abstract — swap for SendGrid/Resend by replacing this class only.
    """
    async def send(self, recipient: str, body: str, subject: str | None = None, **_) -> tuple[bool, str | None]:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject or "Techno Kids Notification"
            msg["From"] = settings.GMAIL_SENDER_ADDRESS
            msg["To"] = recipient
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(settings.GMAIL_SENDER_ADDRESS, settings.GMAIL_APP_PASSWORD)
                server.sendmail(settings.GMAIL_SENDER_ADDRESS, recipient, msg.as_string())
            return True, None
        except Exception as e:
            return False, str(e)
```

---

## Phase 4 — Repository & Interface

### [NEW] `interfaces/i_notification_repository.py`
```python
class INotificationRepository(Protocol):
    def get_template_by_name(self, name: str) -> NotificationTemplate | None: ...
    def get_all_templates(self) -> list[NotificationTemplate]: ...
    def create_template(self, ...) -> NotificationTemplate: ...
    def update_template(self, ...) -> NotificationTemplate: ...
    def delete_template(self, id: int) -> None: ...
    def log_notification(self, ...) -> NotificationLog: ...
    def update_log_status(self, log_id: int, status: str, error: str | None) -> None: ...
    def get_logs(self, recipient_id: int | None, limit: int) -> list[NotificationLog]: ...
    def get_report_subscribers(self, report_type: str) -> list[NotificationSubscriber]: ...
```

### [NEW] `repositories/notification_repository.py`

Pure ORM data access. Session injected from service layer (following Finance Pattern).

---

## Phase 5 — NotificationService (Core Orchestrator)

### [NEW] `services/notification_service.py`

```python
class NotificationService:
    """
    Main notification orchestrator.
    
    Responsibilities:
    - Template rendering ({{variable}} substitution)
    - Recipient contact resolution from DB
    - BackgroundTask dispatch (non-blocking)
    - Notification log persistence
    """

    def __init__(self, repo: INotificationRepository):
        self._repo = repo
        self._whatsapp = TwilioWhatsAppDispatcher()
        self._email = GmailEmailDispatcher()

    # ── Transactional (called by other services) ─────────────────────────
    def notify_absence(self, student_id: int, session_name: str, session_date: str, background_tasks: BackgroundTasks) -> None:
        """Queues an absence alert to the student's primary parent. Non-blocking."""

    def notify_enrollment(self, enrollment_id: int, background_tasks: BackgroundTasks) -> None:
        """Queues an enrollment confirmation to the student's primary parent."""

    def notify_payment_receipt(self, receipt_id: int, background_tasks: BackgroundTasks) -> None:
        """Queues a payment receipt notification to the parent."""

    # ── Scheduled Reports (called by report_scheduler) ───────────────────
    async def send_daily_report(self) -> None: ...
    async def send_weekly_report(self) -> None: ...
    async def send_monthly_report(self) -> None: ...

    # ── Bulk Marketing (admin-triggered via API) ──────────────────────────
    def send_bulk(self, parent_ids: list[int], template_name: str, extra_vars: dict, background_tasks: BackgroundTasks) -> int:
        """Queues WhatsApp messages to a list of parents. Returns queued count."""

    # ── Private helpers ──────────────────────────────────────────────────
    def _render(self, template: NotificationTemplate, variables: dict) -> str:
        """Simple {{key}} substitution — no template engine needed."""
        body = template.body
        for key, val in variables.items():
            body = body.replace(f"{{{{{key}}}}}", str(val))
        return body

    def _resolve_parent_contact(self, student_id: int) -> tuple[str | None, str | None]:
        """Returns (phone, email) for primary parent of student."""
```

**Key design decisions:**
- `notify_*` methods are **synchronous** (they just enqueue into `BackgroundTasks`) — callers don't await
- Actual HTTP/SMTP calls happen inside the background task coroutine
- Every dispatch attempt writes a `NotificationLog` record regardless of success/failure

---

## Phase 6 — Scheduler (Zero Dependencies)

### [NEW] `services/report_scheduler.py`

```python
import asyncio
from datetime import datetime

async def start_report_scheduler(notification_service: NotificationService) -> None:
    """
    Self-contained asyncio task. Started once at app lifespan.
    Checks every 60 seconds whether a scheduled report is due.
    Uses a 'last_sent' guard to prevent double-sends on fast restarts.
    """
    last_daily = last_weekly = last_monthly = None

    while True:
        now = datetime.now()

        if now.hour == 8 and now.minute == 0:
            today = now.date()
            if last_daily != today:
                await notification_service.send_daily_report()
                last_daily = today

            if now.weekday() == 0 and last_weekly != today:
                await notification_service.send_weekly_report()
                last_weekly = today

            if now.day == 1 and last_monthly != today:
                await notification_service.send_monthly_report()
                last_monthly = today

        await asyncio.sleep(60)
```

### [MODIFY] `app/api/main.py` — Register lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    notification_service = NotificationService(NotificationRepository())
    asyncio.create_task(start_report_scheduler(notification_service))
    yield
```

---

## Phase 7 — API Routers

### [NEW] `routers/notifications/notifications_router.py`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/notifications/absence` | `require_admin` | Manually trigger absence alert (Option A) |
| `POST` | `/notifications/receipt/{receipt_id}` | `require_admin` | Send receipt notification |
| `GET` | `/notifications/logs` | `require_admin` | All notification logs (paginated) |
| `GET` | `/notifications/logs/parent/{parent_id}` | `require_admin` | Per-parent history |

### [NEW] `routers/notifications/templates_router.py`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/notifications/templates` | `require_admin` | List all templates |
| `GET` | `/notifications/templates/{id}` | `require_admin` | Get single template |
| `POST` | `/notifications/templates` | `require_admin` | Create custom template |
| `PUT` | `/notifications/templates/{id}` | `require_admin` | Update (blocks standard templates) |
| `DELETE` | `/notifications/templates/{id}` | `require_admin` | Delete (blocks standard templates) |

### [NEW] `routers/notifications/bulk_router.py`

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/notifications/bulk` | `require_admin` | Bulk send to parent list |
| `GET` | `/notifications/subscribers` | `require_admin` | List report subscribers |
| `POST` | `/notifications/subscribers` | `require_admin` | Add employee as report recipient |
| `DELETE` | `/notifications/subscribers/{id}` | `require_admin` | Remove subscriber |

---

## Phase 8 — Integration With Existing Services (Light Touch)

### [MODIFY] `app/modules/finance/services/receipt_service.py`

The `create()` method already has a `TODO: Implement when notification tracking is added` comment in `mark_as_sent()`. We inject `NotificationService` similarly to how `StudentActivityService` is injected today — **optional constructor parameter (`TYPE_CHECKING` guarded)**.

```python
class ReceiptService(IReceiptService):
    def __init__(self, uow, activity_svc=None, notification_svc=None):
        self._notification_svc = notification_svc

    def create(self, dto) -> ReceiptFinalizedDTO:
        result = ...  # existing logic
        if self._notification_svc and dto.notify_parent:
            self._notification_svc.notify_payment_receipt(result.receipt_id, background_tasks)
        return result
```

### [MODIFY] `app/modules/enrollments/services/enrollment_service.py`

Same pattern — optional `notification_svc` injected at construction.

### [MODIFY] `app/api/dependencies.py`

```python
from app.modules.notifications.services.notification_service import NotificationService
from app.modules.notifications.repositories.notification_repository import NotificationRepository

def get_notification_service() -> NotificationService:
    return NotificationService(repo=NotificationRepository())

# Update get_receipt_service() to optionally inject notification_svc
def get_receipt_service() -> ReceiptService:
    with FinanceUnitOfWork() as finance_uow, StudentUnitOfWork() as crm_uow:
        activity_svc = StudentActivityService(crm_uow)
        notification_svc = NotificationService(repo=NotificationRepository())
        return ReceiptService(finance_uow, activity_svc=activity_svc, notification_svc=notification_svc)
```

### No modification needed to:
- `AttendanceService` — absence notification is **manually triggered** via its own endpoint (Option A)
- Any analytics services — reports are scheduler-driven

---

## New Dependencies

| Package | Version | Purpose | Where added |
|---|---|---|---|
| `twilio` | `^9.x` | WhatsApp dispatch via Twilio API | `pyproject.toml`, `requirements.txt` |

Everything else uses existing stdlib (`smtplib`, `asyncio`, `email`) or already-present packages (`sqlmodel`, `httpx`).

---

## New Environment Variables

```bash
# .env additions
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886   # Sandbox number initially
GMAIL_SENDER_ADDRESS=yourbusiness@gmail.com
GMAIL_APP_PASSWORD=xxxx xxxx xxxx xxxx       # Gmail App Password (not login password)
REPORT_RECIPIENT_EMAIL=admin@technokids.com  # Default admin report target
```

---

## Execution Phases

| Phase | Deliverable | Files Changed |
|---|---|---|
| 1 | DB models + migration + seed templates | 3 new model files, 1 migration SQL |
| 2 | Abstract dispatcher interface | 1 new interface file |
| 3 | Twilio + Gmail dispatchers | 2 new dispatcher files |
| 4 | Repository + interface | 2 new files |
| 5 | `NotificationService` orchestrator | 1 new service file |
| 6 | Scheduler + `main.py` lifespan | 1 new file, 1 modified |
| 7 | API routers + `dependencies.py` | 3 new router files, 1 modified |  
| 8 | Integration hooks (Finance, Enrollment) | 2 modified service files + dependencies |
| 9 | Tests | 1 new test file |

---

## Verification Plan

### Automated Tests (`tests/api/notifications/`)
- Template CRUD endpoints (create, list, update, block delete of standard)
- Bulk send endpoint returns correct queued count
- Log endpoint returns correct records after send
- Absence notification endpoint correctly resolves parent

### Manual Verification
1. Set up Twilio sandbox, add phone to sandbox participants
2. POST `/notifications/absence` → verify WhatsApp message received
3. POST `/notifications/bulk` → verify multiple messages received
4. POST `/notifications/templates` → create custom template, use in send
5. Wait for scheduler tick → verify email received at 08:00

---

## What is NOT in Scope (Backlog)

- Campaign management (tracking bulk send performance)
- Opt-in/opt-out management (parent preference tracking)
- Push notifications (mobile app — future React Native frontend)
- WhatsApp template approval automation
- Retry queue for failed sends (currently logged as FAILED, manual retry)
