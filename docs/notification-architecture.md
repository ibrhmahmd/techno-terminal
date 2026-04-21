# Notification Service Architecture

Comprehensive documentation of the modular notification system for the CRM application.

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Data Model](#2-data-model)
3. [Service Hierarchy](#3-service-hierarchy)
4. [Notification Workflows](#4-notification-workflows)
5. [Design Decisions](#5-design-decisions)
6. [File Reference](#6-file-reference)

---

## 1. Architecture Overview

### Module Structure

```
app/modules/notifications/
├── __init__.py
├── interfaces/
│   └── i_notification_repository.py      # Protocol contracts
├── models/
│   ├── notification_template.py           # Template entity
│   └── notification_log.py                # Audit log entity
├── schemas/
│   ├── admin_settings_dto.py              # Admin settings DTOs
│   └── template_dto.py                    # Template DTOs
├── repositories/
│   ├── notification_repository.py         # Data access layer
│   └── admin_settings_repository.py       # Admin settings data access
├── dispatchers/
│   ├── i_dispatcher.py                    # Abstract dispatcher interface
│   ├── email_dispatcher.py                # Gmail SMTP implementation
│   └── whatsapp_dispatcher.py             # Twilio WhatsApp implementation
└── services/
    ├── __init__.py                        # Exports all services
    ├── base_notification_service.py       # Shared helpers (contact resolution, dispatch)
    ├── notification_service.py            # Main orchestrator (facade)
    ├── enrollment_notifications.py      # Enrollment lifecycle
    ├── payment_notifications.py          # Payment events
    ├── report_notifications.py            # Scheduled reports
    └── competition_notifications.py     # Competition events (NEW)
```

### Service Hierarchy Diagram

```mermaid
graph TD
    NS[NotificationService<br/>Orchestrator/Facade] --> EN[EnrollmentNotificationService]
    NS --> PN[PaymentNotificationService]
    NS --> RN[ReportNotificationService]
    NS --> CN[CompetitionNotificationService<br/>NEW]
    
    EN --> BNS[BaseNotificationService]
    PN --> BNS
    RN --> BNS
    CN --> BNS
    
    BNS --> NR[NotificationRepository]
    BNS --> ED[GmailEmailDispatcher]
    BNS --> WD[TwilioWhatsAppDispatcher]
    
    subgraph "Infrastructure Layer"
        NR
        ED
        WD
    end
    
    subgraph "Domain Services"
        EN
        PN
        RN
        CN
    end
    
    subgraph "Facade"
        NS
    end
```

---

## 2. Data Model

### Entity Relationship Diagram

```mermaid
erDiagram
    NOTIFICATION_TEMPLATE ||--o{ NOTIFICATION_LOG : generates
    NOTIFICATION_TEMPLATE {
        int id PK
        string name UK
        string code UK
        string channel "EMAIL|WHATSAPP"
        string subject
        text body
        string variables
        boolean is_standard
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    NOTIFICATION_LOG {
        int id PK
        int template_id FK
        string channel
        string recipient_type "PARENT|ADMIN|EMPLOYEE"
        int recipient_id
        string recipient_contact
        string status "PENDING|SENT|FAILED"
        text body
        string subject
        string error_message
        datetime created_at
        datetime sent_at
    }
    
    ADMIN_NOTIFICATION_SETTINGS {
        int id PK
        int admin_id FK
        string notification_type
        boolean is_enabled
        string channel
        datetime created_at
        datetime updated_at
    }
    
    USERS ||--o{ ADMIN_NOTIFICATION_SETTINGS : configures
    
    NOTIFICATION_ADDITIONAL_RECIPIENTS {
        int id PK
        int admin_id FK
        string email
        string label
        string[] notification_types
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    ADMIN_NOTIFICATION_SETTINGS ||--o{ NOTIFICATION_ADDITIONAL_RECIPIENTS : has
```

### Template Variables

| Template | Variables |
|----------|-----------|
| `enrollment_confirmation` | `parent_name`, `student_name`, `group_name`, `level_number`, `instructor_name`, `enrollment_id` |
| `enrollment_completed` | `parent_name`, `student_name`, `group_name`, `level_number`, `completion_date`, `enrollment_id` |
| `enrollment_dropped` | `parent_name`, `student_name`, `group_name`, `reason`, `enrollment_id` |
| `enrollment_transferred` | `parent_name`, `student_name`, `from_group_name`, `to_group_name`, `from_enrollment_id`, `to_enrollment_id` |
| `level_progression` | `parent_name`, `student_name`, `old_level`, `new_level`, `group_name`, `enrollment_id` |
| `payment_receipt` | `parent_name`, `student_name`, `amount`, `receipt_number`, `receipt_id` |
| `payment_reminder` | `parent_name`, `student_name`, `amount_due`, `due_date` |
| `daily_report` | `date`, `total_revenue`, `new_enrollments`, `sessions_held`, `absent_count` |
| `weekly_report` | `week_start`, `week_end`, `total_revenue`, `new_students`, `attendance_rate` |
| `monthly_report` | `month`, `total_revenue`, `new_enrollments`, `active_students` |
| `competition_team_registration` | `student_name`, `team_name`, `competition_name`, `category` |
| `competition_fee_payment` | `student_name`, `team_name`, `competition_name`, `amount`, `receipt_number` |
| `competition_placement` | `student_name`, `team_name`, `competition_name`, `placement_rank`, `placement_label`, `rank_display` |

---

## 3. Service Hierarchy

### BaseNotificationService

Core infrastructure class providing:

```mermaid
classDiagram
    class BaseNotificationService {
        +NotificationRepository _repo
        +GmailEmailDispatcher _email
        +TwilioWhatsAppDispatcher _whatsapp
        +_resolve_contact(student_id, channel) Tuple
        +_resolve_admin_contacts() list
        +_render_template(template, variables) str
        +_dispatch(template, channel, recipient_type, recipient_id, contact, variables) None
    }
    
    class EnrollmentNotificationService {
        +notify_enrollment_created()
        +notify_enrollment_completed()
        +notify_enrollment_dropped()
        +notify_enrollment_transferred()
        +notify_level_progression()
        -_process_created()
        -_process_completed()
        -_process_dropped()
        -_process_transferred()
        -_process_progression()
        -_get_group_name()
        -_get_instructor_name()
        -_get_student_name()
    }
    
    class PaymentNotificationService {
        +notify_payment_received()
        +notify_payment_reminder()
        -_process_received()
        -_process_reminder()
    }
    
    class ReportNotificationService {
        +send_daily_report()
        +send_weekly_report()
        +send_monthly_report()
        +send_bulk()
        -_fetch_daily_aggregates()
        -_fetch_weekly_aggregates()
        -_fetch_monthly_aggregates()
    }
    
    class CompetitionNotificationService {
        +notify_team_registration()
        +notify_competition_fee_paid()
        +notify_placement_announcement()
        -_process_team_registration()
        -_process_fee_payment()
        -_process_placement()
        -_resolve_parent_contacts()
        -_dispatch_notifications()
        -_get_ordinal_suffix()
    }
    
    BaseNotificationService <|-- EnrollmentNotificationService
    BaseNotificationService <|-- PaymentNotificationService
    BaseNotificationService <|-- ReportNotificationService
    BaseNotificationService <|-- CompetitionNotificationService
```

---

## 4. Notification Workflows

### 4.1 Enrollment Notification Flow

```mermaid
sequenceDiagram
    participant Client as EnrollmentService
    participant NS as NotificationService
    participant EN as EnrollmentNotificationService
    participant BNS as BaseNotificationService
    participant Repo as NotificationRepository
    participant DB as Database
    participant Email as GmailEmailDispatcher
    
    Client->>NS: notify_enrollment_created()
    NS->>EN: notify_enrollment_created()
    EN->>EN: background_tasks.add_task(_process_created)
    
    par Async Processing
        EN->>Repo: get_template_by_name("enrollment_confirmation")
        Repo->>DB: SELECT template
        DB-->>Repo: template
        Repo-->>EN: template
        
        EN->>BNS: _resolve_admin_contacts()
        BNS->>DB: SELECT users WHERE role='admin'
        DB-->>BNS: admin list
        BNS-->>EN: [(email, id), ...]
        
        EN->>EN: _get_student_name()
        EN->>EN: _get_group_name()
        EN->>EN: _get_instructor_name()
        
        loop For each admin
            EN->>BNS: _dispatch(template, "EMAIL", "ADMIN", admin_id, email, variables)
            BNS->>BNS: _render_template()
            BNS->>Repo: create_log()
            Repo->>DB: INSERT notification_log
            BNS->>Email: send(email, body, subject)
            Email-->>BNS: (success, error)
            BNS->>Repo: update_log_status()
        end
    end
```

### 4.2 Payment Notification Flow

```mermaid
sequenceDiagram
    participant Client as PaymentService
    participant NS as NotificationService
    participant PN as PaymentNotificationService
    participant BNS as BaseNotificationService
    participant Repo as NotificationRepository
    participant DB as Database
    participant Email as GmailEmailDispatcher
    
    Client->>NS: payment.notify_payment_received()
    NS->>PN: notify_payment_received()
    PN->>PN: background_tasks.add_task(_process_received)
    
    par Async Processing
        PN->>Repo: get_template_by_name("payment_receipt")
        Repo->>DB: SELECT template
        DB-->>Repo: template
        
        PN->>BNS: _resolve_admin_contacts()
        BNS->>DB: SELECT users WHERE role='admin'
        DB-->>BNS: admin list
        BNS-->>PN: [(email, id), ...]
        
        PN->>DB: SELECT student name
        DB-->>PN: student_name
        
        loop For each admin
            PN->>BNS: _dispatch(template, "EMAIL", "ADMIN", admin_id, email, variables)
            BNS->>Repo: create_log()
            Repo->>DB: INSERT notification_log
            BNS->>Email: send()
            Email-->>BNS: (success, error)
            BNS->>Repo: update_log_status()
        end
    end
```

### 4.3 Report Notification Flow

```mermaid
sequenceDiagram
    participant Scheduler as ReportScheduler
    participant NS as NotificationService
    participant RN as ReportNotificationService
    participant BNS as BaseNotificationService
    participant Analytics as AnalyticsServices
    participant Repo as NotificationRepository
    participant DB as Database
    participant Email as GmailEmailDispatcher
    
    Scheduler->>Scheduler: Check time (08:00 local)
    Scheduler->>NS: send_daily_report()
    NS->>RN: send_daily_report()
    
    RN->>Repo: get_template_by_name("daily_report")
    Repo->>DB: SELECT template
    DB-->>Repo: template
    
    RN->>BNS: _resolve_admin_contacts()
    BNS->>DB: SELECT users WHERE role='admin'
    DB-->>BNS: admin list
    BNS-->>RN: [(email, id), ...]
    
    RN->>Analytics: _fetch_daily_aggregates()
    Analytics->>DB: Aggregate queries
    DB-->>Analytics: metrics
    Analytics-->>RN: {revenue, enrollments, sessions, absences}
    
    loop For each admin
        RN->>BNS: _dispatch(template, "EMAIL", "ADMIN", admin_id, email, variables)
        BNS->>Repo: create_log()
        Repo->>DB: INSERT notification_log
        BNS->>Email: send()
        Email-->>BNS: result
        BNS->>Repo: update_log_status()
    end
```

### 4.4 Competition Notification Flow (NEW)

```mermaid
sequenceDiagram
    participant Client as CompetitionService
    participant CN as CompetitionNotificationService
    participant Repo as NotificationRepository
    participant DB as Database
    participant Email as GmailEmailDispatcher
    
    Client->>CN: notify_team_registration()
    CN->>CN: background_tasks.add_task(_process_team_registration)
    
    par Async Processing
        CN->>Repo: get_template_by_name("competition_team_registration")
        Repo->>DB: SELECT template
        DB-->>Repo: template
        
        CN->>CN: _resolve_parent_contacts(student_id)
        CN->>DB: SELECT parent via StudentParent
        DB-->>CN: {email, parent_id, student_name}
        
        CN->>CN: _render_template()
        
        CN->>CN: _dispatch_notifications()
        CN->>Repo: create_log()
        Repo->>DB: INSERT notification_log
        CN->>Email: send()
        Email-->>CN: result
    end
```

### 4.5 Dispatch Flow (Core Mechanism)

```mermaid
flowchart TD
    A[Receive dispatch call] --> B[Render template with variables]
    B --> C{Channel?}
    
    C -->|EMAIL| D[Call GmailEmailDispatcher.send]
    C -->|WHATSAPP| E[Log: WhatsApp disabled]
    C -->|Other| F[Return Unknown channel error]
    
    D --> G{Send success?}
    E --> H[Mark success - skip retry]
    
    G -->|Yes| I[Status: SENT]
    G -->|No| J[Status: FAILED]
    
    I --> K[Update notification_log]
    J --> K
    H --> K
    
    K --> L[Log result]
    L --> M[Return]
    
    F --> M
```

---

## 5. Design Decisions

### 5.1 Modular Service Architecture

**Decision:** Split monolithic `NotificationService` into domain-specific services.

**Rationale:**
- Single Responsibility: Each service handles one notification domain
- Maintainability: Changes to enrollment notifications don't affect payment logic
- Testability: Smaller classes are easier to unit test
- Extensibility: New domains (like competitions) can be added without touching existing code

### 5.2 FastAPI BackgroundTasks

**Decision:** Use `BackgroundTasks` for async notification processing.

**Rationale:**
- No external message queue needed (Redis/RabbitMQ)
- Simple deployment and operations
- Sufficient for current volume (<1000 notifications/day)
- Can be upgraded to Celery/RQ later without API changes

### 5.3 Admin-First Notification Strategy

**Decision:** Send all notifications to admin emails, disable parent notifications.

**Rationale:**
- Business requirement: Admins need visibility into all system events
- WhatsApp integration not yet ready
- Parent code preserved as commented blocks for easy re-enabling
- Future: Admin preference panel to control which notifications each admin receives

### 5.4 Template Variable System

**Decision:** Simple `{{variable}}` substitution, no complex templating engine.

**Rationale:**
- Easy to understand and debug
- No external dependencies (Jinja2, etc.)
- Sufficient for current needs
- Variables stored as JSON array in database

### 5.5 Contact Resolution Strategy

**Decision:** Two resolution paths:
1. `_resolve_contact()` - for parent contact (preserved, disabled)
2. `_resolve_admin_contacts()` - for admin emails (current)

**Rationale:**
- Clean separation of concerns
- Easy to switch between modes
- Admin resolution queries `users` table by `role='admin'`

---

## 6. File Reference

### Core Files

| File | Purpose | Key Classes/Functions |
|------|---------|---------------------|
| `app/modules/notifications/services/notification_service.py` | Main orchestrator | `NotificationService` - facade over domain services |
| `app/modules/notifications/services/base_notification_service.py` | Shared infrastructure | `BaseNotificationService` - contact resolution, dispatch |
| `app/modules/notifications/services/enrollment_notifications.py` | Enrollment lifecycle | `EnrollmentNotificationService` - 5 notification types |
| `app/modules/notifications/services/payment_notifications.py` | Payment events | `PaymentNotificationService` - 2 notification types |
| `app/modules/notifications/services/report_notifications.py` | Scheduled reports | `ReportNotificationService` - 3 report types + bulk |
| `app/modules/notifications/services/competition_notifications.py` | Competition events | `CompetitionNotificationService` - 3 notification types (NEW) |

### API Routers

| File | Purpose | Base Path |
|------|---------|-----------|
| `app/api/routers/notifications/admin_settings_router.py` | Admin settings & additional recipients | `/api/v1/notifications/admin` |
| `app/api/routers/notifications/templates_router.py` | Template CRUD operations | `/api/v1/notifications/templates` |
| `app/api/routers/notifications/bulk_router.py` | Bulk messaging | `/api/v1/notifications/bulk` |
| `app/api/routers/notifications/notifications_router.py` | Notification logs & history | `/api/v1/notifications/logs` |

### Infrastructure Files

| File | Purpose |
|------|---------|
| `app/modules/notifications/repositories/notification_repository.py` | Data access for templates and logs |
| `app/modules/notifications/dispatchers/email_dispatcher.py` | Gmail SMTP implementation |
| `app/modules/notifications/dispatchers/whatsapp_dispatcher.py` | Twilio WhatsApp (currently disabled) |
| `app/modules/notifications/dispatchers/i_dispatcher.py` | Protocol interface for dispatchers |
| `app/modules/notifications/interfaces/i_notification_repository.py` | Protocol for repository |

### Models

| File | Entity |
|------|--------|
| `app/modules/notifications/models/notification_template.py` | `NotificationTemplate` |
| `app/modules/notifications/models/notification_log.py` | `NotificationLog` |

### Database Migrations

| File | Purpose |
|------|---------|
| `db/migrations/020_notification_templates.sql` | Initial templates (enrollment, payment, reports) |
| `db/migrations/034_notification_templates.sql` | Extended templates |
| `db/migrations/038_admin_notification_settings.sql` | Admin notification preferences table |
| `db/migrations/039_notification_additional_recipients.sql` | Additional email recipients table |
| `db/migrations/040_competition_templates.sql` | Competition notification templates |

### Scheduler

| File | Purpose |
|------|---------|
| `app/modules/notifications/services/report_scheduler.py` | Asyncio task for scheduled reports |

---

## Appendix: Method Signatures

### EnrollmentNotificationService

```python
def notify_enrollment_created(
    self, student_id: int, enrollment_id: int, group_id: int,
    level_number: int, background_tasks: BackgroundTasks
) -> None

def notify_enrollment_completed(
    self, student_id: int, enrollment_id: int, group_id: int,
    level_number: int, completion_date: datetime, background_tasks: BackgroundTasks
) -> None

def notify_enrollment_dropped(
    self, student_id: int, enrollment_id: int, group_id: int,
    reason: Optional[str], dropped_by: Optional[int], background_tasks: BackgroundTasks
) -> None

def notify_enrollment_transferred(
    self, student_id: int, from_enrollment_id: int, to_enrollment_id: int,
    from_group_id: int, to_group_id: int, transferred_by: Optional[int],
    background_tasks: BackgroundTasks
) -> None

def notify_level_progression(
    self, student_id: int, old_level: int, new_level: int,
    group_id: int, enrollment_id: int, background_tasks: BackgroundTasks
) -> None
```

### PaymentNotificationService

```python
def notify_payment_received(
    self, receipt_id: int, student_id: int, amount: str,
    receipt_number: str, background_tasks: BackgroundTasks
) -> None

def notify_payment_reminder(
    self, student_id: int, amount_due: str, due_date: str,
    background_tasks: BackgroundTasks
) -> None
```

### ReportNotificationService

```python
async def send_daily_report(self) -> None
async def send_weekly_report(self) -> None
async def send_monthly_report(self) -> None
def send_bulk(
    self, parent_ids: list[int], template_name: str, 
    extra_vars: dict, background_tasks
) -> int
```

### CompetitionNotificationService (NEW)

```python
def notify_team_registration(
    self, student_id: int, team_id: int, team_name: str,
    competition_name: str, category: str, subcategory: Optional[str],
    background_tasks: BackgroundTasks
) -> None

def notify_competition_fee_paid(
    self, student_id: int, team_id: int, team_name: str,
    competition_name: str, amount: Decimal, receipt_number: str,
    background_tasks: BackgroundTasks
) -> None

def notify_placement_announcement(
    self, student_id: int, team_id: int, team_name: str,
    competition_name: str, placement_rank: int,
    placement_label: Optional[str], background_tasks: BackgroundTasks
) -> None
```

---

*Last Updated: April 2026*
