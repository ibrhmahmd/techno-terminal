# Notification Service Architecture Redesign

A comprehensive analysis of notification architecture patterns for scaling to support payments, enrollments, attendance, on-demand reports, scheduled reports, and future notification types.

---

## Executive Summary

Compare 4 architectural patterns for notification service growth and recommend **Event-Driven Architecture with Strategy Pattern** as the optimal solution for this codebase.

---

## Current Architecture Analysis

### Existing Pattern: Monolithic Service with Direct Dispatch

```
┌─────────────────────────────────────────────────────────┐
│              NotificationService (777 lines)             │
├─────────────────────────────────────────────────────────┤
│  • notify_absence()          • _process_*_notification()│
│  • notify_enrollment()       • _dispatch_internal()     │
│  • notify_payment_receipt()  • _resolve_contact_info()  │
│  • notify_level_progression()• send_daily_report()      │
│  • notify_enrollment_completed()• send_weekly_report()  │
│  • notify_enrollment_dropped() • send_monthly_report()  │
│  • notify_enrollment_transferred()• send_bulk()         │
│  • _fetch_*_aggregates()                                │
└─────────────────────────────────────────────────────────┘
```

**Problems with Current Design:**

| Issue | Impact | Example |
|-------|--------|---------|
| **God Class** | 777 lines, violates SRP | All notification logic in one file |
| **Tight Coupling** | Hard to add new notification types | Must modify NotificationService for each new type |
| **Mixed Concerns** | Business logic + Dispatch + Data fetching | Analytics queries inside notification service |
| **Scalability Bottleneck** | Cannot handle high volume | Single-threaded background tasks |
| **Testing Complexity** | Hard to unit test | Requires full service instantiation |
| **Template Sprawl** | Database template codes scattered | No namespace/type organization |

---

## Pattern Comparison

### Pattern 1: Strategy Pattern with Composition

**Concept:** Separate notification types into interchangeable strategies.

```
┌─────────────────────────────────────────────────────────┐
│              NotificationOrchestrator                   │
├─────────────────────────────────────────────────────────┤
│  - strategy_map: Dict[NotificationType, Strategy]       │
│  - dispatchers: Dict[Channel, IDispatcher]              │
├─────────────────────────────────────────────────────────┤
│  + send(notification_type, context, channel)            │
│  + register_strategy(type, strategy)                    │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  AbsenceStrategy│  │EnrollmentStrategy│  │ PaymentStrategy │
│  ───────────────│  │ ────────────────│  │ ────────────────│
│  + prepare_data()│  │ + prepare_data() │  │ + prepare_data()│
│  + get_template()│  │ + get_template() │  │ + get_template()│
│  + get_recipient()│  │ + get_recipient()│  │ + get_recipient()│
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

**Pros:**
- ✅ Open/Closed Principle: Add types without modifying orchestrator
- ✅ Single Responsibility: Each strategy handles one notification type
- ✅ Testability: Mock individual strategies
- ✅ Type Safety: Generic NotificationContext[T]

**Cons:**
- ❌ More boilerplate (interface + implementations)
- ❌ Service layer needs to know strategy types
- ❌ Still synchronous (FastAPI BackgroundTasks limitation)

**Complexity:** Medium
**Fit for Codebase:** Good (matches existing repository pattern)

---

### Pattern 2: Event-Driven Architecture (Pub/Sub)

**Concept:** Domain events trigger notification handlers asynchronously.

```
┌─────────────────────────────────────────────────────────┐
│              Business Services (Enrollments, etc)       │
├─────────────────────────────────────────────────────────┤
│  enroll_student() {                                     │
│    # ... business logic ...                             │
│    event_bus.publish(EnrollmentCreatedEvent(...))      │
│  }                                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   Event Bus (async)                      │
├─────────────────────────────────────────────────────────┤
│  subscribers: Dict[EventType, List[Handler]]             │
├─────────────────────────────────────────────────────────┤
│  + publish(event)  →  route to all subscribers         │
└─────────────────────────────────────────────────────────┘
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│EmailHandler  │  │WhatsAppHandler│  │AuditHandler │
│──────────────│  │───────────────│  │──────────────│
│+ handle(event)│ │+ handle(event)│  │+ handle(event)│
└──────────────┘  └──────────────┘  └──────────────┘
```

**Pros:**
- ✅ True decoupling: Services don't know about notifications
- ✅ Multiple handlers per event (Email + Audit + Webhook)
- ✅ Easy to add new notification channels
- ✅ Natural for scheduled reports (cron triggers events)
- ✅ Supports retries and dead-letter queues

**Cons:**
- ❌ More complex infrastructure (event bus)
- ❌ Eventual consistency (not immediate feedback)
- ❌ Harder to trace/debug (async flow)
- ❌ Requires message queue for production (Redis/RabbitMQ)

**Complexity:** High
**Fit for Codebase:** Excellent (aligns with audit logging needs)

---

### Pattern 3: Chain of Responsibility with Middleware

**Concept:** Notification passes through a chain of processors (validation → enrichment → dispatch).

```
┌─────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Event  │───▶│  Validation  │───▶│  Enrichment  │───▶│   Dispatch   │
│  Input  │    │  Middleware  │    │  Middleware  │    │  Middleware  │
└─────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                      │                   │                   │
                      ▼                   ▼                   ▼
                 Check limits       Resolve parent      Send via channel
                 Validate template   Fetch group info    Log to database
```

**Pros:**
- ✅ Pipeline pattern: Clean separation of concerns
- ✅ Reusable middleware components
- ✅ Easy to add/remove steps
- ✅ Rate limiting fits naturally

**Cons:**
- ❌ Overkill for simple notifications
- ❌ Debugging chain failures is hard
- ❌ Performance overhead per notification
- ❌ Not ideal for different notification types

**Complexity:** Medium-High
**Fit for Codebase:** Poor (unnecessary for current requirements)

---

### Pattern 4: Factory + Template Method Pattern

**Concept:** Abstract base class defines workflow, subclasses customize specific steps.

```
┌─────────────────────────────────────────────────────────┐
│          AbstractNotificationWorkflow                    │
│  ─────────────────────────────────────────────────────  │
│  # Template Method                                        │
│  + send(context):                                         │
│    data = prepare_data(context)  # abstract               │
│    template = get_template()     # abstract               │
│    recipient = resolve_recipient(context)  # abstract     │
│    dispatch(recipient, template, data)  # concrete        │
│    log_notification()  # concrete                         │
├─────────────────────────────────────────────────────────┤
│  # Hook Methods                                           │
│  - pre_send()  # optional override                        │
│  - post_send() # optional override                        │
└─────────────────────────────────────────────────────────┘
         │
    ┌────┴────┬───────────┬───────────────┐
    ▼         ▼           ▼               ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│Absence │ │Payment │ │Enrollment│ │Attendance│
│Workflow│ │Workflow│ │ Workflow │ │ Workflow │
└────────┘ └────────┘ └──────────┘ └──────────┘
```

**Pros:**
- ✅ Inheritance-based reuse
- ✅ Common workflow enforced
- ✅ Customization via override

**Cons:**
- ❌ Brittle inheritance hierarchy
- ❌ Hard to share behavior across unrelated types
- ❌ Diamond problem risk
- ❌ Less flexible than composition

**Complexity:** Medium
**Fit for Codebase:** Poor (Python favors composition over inheritance)

---

## Recommended Architecture: Hybrid Event-Driven + Strategy

### Rationale

Combine **Event-Driven** decoupling with **Strategy** pattern flexibility:

1. **Event-Driven Core**: Domain services emit events, notification system reacts
2. **Strategy Handlers**: Each notification type has a strategy implementation
3. **Channel Abstraction**: Dispatchers stay swappable (current pattern preserved)

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DOMAIN LAYER                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Enrollment │  │   Payment   │  │  Attendance │  │   Reports   │        │
│  │   Service   │  │   Service   │  │   Service   │  │   Service   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │               │
│         └────────────────┴────────────────┴────────────────┘               │
│                                   │                                         │
│                         emit(DomainEvent)                                   │
└───────────────────────────────────┼───────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EVENT BUS LAYER                                       │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  NotificationEventBus (singleton, async)                                ││
│  │  ─────────────────────────────────────────────────────────────────────  ││
│  │  handlers: Dict[EventType, List[NotificationHandler]]                   ││
│  │                                                                         ││
│  │  + publish(event: DomainEvent) → await handlers                         ││
│  │  + subscribe(event_type, handler: NotificationHandler)                  ││
│  │  + unsubscribe(event_type, handler)                                     ││
│  └─────────────────────────────────────────────────────────────────────────┘│
└───────────────────────────────────┬───────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     HANDLER LAYER (Strategies)                               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│  │ EnrollmentHandler│ │  PaymentHandler  │ │  AbsenceHandler  │            │
│  │ ──────────────── │ │ ──────────────── │ │ ──────────────── │            │
│  │ implements:      │ │ implements:      │ │ implements:      │            │
│  │ NotificationHandler│ │ NotificationHandler│ │ NotificationHandler│            │
│  │                  │ │                  │ │                  │            │
│  │ + can_handle()   │ │ + can_handle()   │ │ + can_handle()   │            │
│  │ + handle(event)  │ │ + handle(event)  │ │ + handle(event)  │            │
│  │   → validate     │ │   → validate     │ │   → validate     │            │
│  │   → enrich data  │ │   → enrich data  │ │   → enrich data  │            │
│  │   → get template │ │   → get template │ │   → get template │            │
│  │   → dispatch     │ │   → dispatch     │ │   → dispatch     │            │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘            │
│                                                                             │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│  │ ReportHandler    │ │  BulkHandler     │ │  RetryHandler    │            │
│  │ (scheduled)      │ │  (marketing)     │ │  (dead letter)   │            │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DISPATCH LAYER (Preserved)                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐              │
│  │ EmailDispatcher │  │WhatsAppDispatcher│  │PushDispatcher   │ (future)     │
│  │ ─────────────── │  │ ──────────────── │  │ ─────────────── │              │
│  │ + send()        │  │ + send()        │  │ + send()        │              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Roadmap

### Phase 1: Foundation (2-3 days)

1. **Create Event Bus**
   ```
   app/modules/notifications/events/
   ├── __init__.py
   ├── event_bus.py          # NotificationEventBus
   ├── domain_events.py      # EnrollmentCreatedEvent, etc.
   └── event_types.py        # EventType enum
   ```

2. **Define Handler Interface**
   ```
   app/modules/notifications/handlers/
   ├── __init__.py
   ├── base_handler.py       # NotificationHandler protocol
   ├── enrollment_handler.py # EnrollmentCreatedHandler
   ├── payment_handler.py    # PaymentReceivedHandler
   └── absence_handler.py    # AbsenceAlertHandler
   ```

3. **Refactor Dispatchers** (preserve existing)
   ```
   app/modules/notifications/dispatchers/
   ├── __init__.py
   ├── i_dispatcher.py       # (existing)
   ├── email_dispatcher.py   # (existing)
   └── whatsapp_dispatcher.py # (existing)
   ```

### Phase 2: Migration (3-4 days)

1. **Migrate Existing Notifications**
   - Move `notify_enrollment()` → `EnrollmentCreatedHandler`
   - Move `notify_payment_receipt()` → `PaymentReceivedHandler`
   - Move `notify_absence()` → `AbsenceAlertHandler`
   - Move scheduled reports → `ReportHandler`

2. **Update Service Layer**
   - Remove `NotificationService` dependency from business services
   - Add `EventBus` dependency instead
   - Emit events after business operations

3. **Template Organization**
   ```
   notification_templates table:
   - Add: category (enrollment, payment, attendance, report)
   - Add: event_type (created, completed, dropped, transferred)
   - Existing: name, channel, body, variables
   ```

### Phase 3: Enhancements (2-3 days)

1. **Add New Notification Types**
   - `AttendanceSummaryHandler` (daily/weekly)
   - `PaymentReminderHandler` (scheduled)
   - `LevelProgressionHandler` (enrollment events)

2. **Retry & Dead Letter Queue**
   - Failed notifications → retry queue
   - Max retries → dead letter log
   - Manual retry endpoint

3. **Rate Limiting**
   - Per-parent rate limiter
   - Bulk notification throttling

---

## Code Example: New Architecture

### 1. Domain Event Definition

```python
# app/modules/notifications/events/domain_events.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass(frozen=True)
class EnrollmentCreatedEvent:
    student_id: int
    enrollment_id: int
    group_id: int
    level_number: int
    enrolled_at: datetime
    performed_by: Optional[int] = None

@dataclass(frozen=True)
class PaymentReceivedEvent:
    receipt_id: int
    student_id: int
    amount: float
    receipt_number: str
    paid_at: datetime
```

### 2. Event Bus Implementation

```python
# app/modules/notifications/events/event_bus.py
import asyncio
from typing import Dict, List, Callable, Any
from dataclasses import is_dataclass
import logging

logger = logging.getLogger(__name__)

class NotificationEventBus:
    """
    Async event bus for notification domain events.
    
    Usage:
        bus = NotificationEventBus()
        bus.subscribe(EnrollmentCreatedEvent, enrollment_handler)
        await bus.publish(EnrollmentCreatedEvent(...))
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers: Dict[type, List[Callable]] = {}
        return cls._instance
    
    def subscribe(self, event_type: type, handler: Callable[[Any], None]):
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Handler {handler.__name__} subscribed to {event_type.__name__}")
    
    def unsubscribe(self, event_type: type, handler: Callable[[Any], None]):
        """Unsubscribe a handler from an event type."""
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
    
    async def publish(self, event: Any):
        """Publish an event to all subscribed handlers (async)."""
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers for event type: {event_type.__name__}")
            return
        
        # Run handlers concurrently
        await asyncio.gather(
            *[self._run_handler(handler, event) for handler in handlers],
            return_exceptions=True
        )
    
    async def _run_handler(self, handler: Callable, event: Any):
        """Run a single handler with error isolation."""
        try:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result
        except Exception as e:
            logger.exception(f"Handler {handler.__name__} failed for {type(event).__name__}: {e}")
```

### 3. Handler Implementation

```python
# app/modules/notifications/handlers/enrollment_handler.py
from typing import Protocol
from dataclasses import dataclass

from app.modules.notifications.events.domain_events import (
    EnrollmentCreatedEvent,
    EnrollmentCompletedEvent,
    EnrollmentDroppedEvent,
    EnrollmentTransferredEvent,
)
from app.modules.notifications.dispatchers.i_dispatcher import IMessageDispatcher
from app.modules.notifications.repositories.notification_repository import NotificationRepository

class NotificationHandler(Protocol):
    """Protocol for all notification handlers."""
    
    async def handle(self, event: Any) -> None:
        """Process a notification event."""
        ...
    
    def can_handle(self, event_type: type) -> bool:
        """Check if this handler supports the event type."""
        ...


class EnrollmentNotificationHandler:
    """
    Handles all enrollment-related notifications.
    
    Supports: created, completed, dropped, transferred events.
    """
    
    def __init__(
        self,
        repo: NotificationRepository,
        email_dispatcher: IMessageDispatcher,
        whatsapp_dispatcher: IMessageDispatcher,
    ):
        self._repo = repo
        self._email = email_dispatcher
        self._whatsapp = whatsapp_dispatcher
        self._supported_events = {
            EnrollmentCreatedEvent: self._handle_created,
            EnrollmentCompletedEvent: self._handle_completed,
            EnrollmentDroppedEvent: self._handle_dropped,
            EnrollmentTransferredEvent: self._handle_transferred,
        }
    
    def can_handle(self, event_type: type) -> bool:
        return event_type in self._supported_events
    
    async def handle(self, event: Any) -> None:
        """Route to appropriate handler method."""
        handler = self._supported_events.get(type(event))
        if handler:
            await handler(event)
    
    async def _handle_created(self, event: EnrollmentCreatedEvent) -> None:
        """Send enrollment confirmation email."""
        template = await self._repo.get_template_by_code("ENROLLMENT_CREATED")
        if not template:
            return
        
        # Resolve parent contact
        email, parent_id, parent_name, student_name = self._resolve_parent_email(event.student_id)
        if not email:
            return
        
        # Enrich data
        group_info = self._get_group_info(event.group_id)
        
        variables = {
            "parent_name": parent_name,
            "student_name": student_name,
            "group_name": group_info.name,
            "level_number": str(event.level_number),
            "enrollment_date": event.enrolled_at.strftime("%Y-%m-%d"),
            "instructor_name": group_info.instructor_name,
        }
        
        # Dispatch
        await self._dispatch(template, "EMAIL", parent_id, email, variables)
    
    async def _handle_completed(self, event: EnrollmentCompletedEvent) -> None:
        """Send enrollment completion email."""
        template = await self._repo.get_template_by_code("ENROLLMENT_COMPLETED")
        # ... similar pattern ...
    
    async def _handle_dropped(self, event: EnrollmentDroppedEvent) -> None:
        """Send enrollment drop email."""
        template = await self._repo.get_template_by_code("ENROLLMENT_DROPPED")
        # ... similar pattern ...
    
    async def _handle_transferred(self, event: EnrollmentTransferredEvent) -> None:
        """Send enrollment transfer email."""
        template = await self._repo.get_template_by_code("ENROLLMENT_TRANSFERRED")
        # ... similar pattern ...
    
    def _resolve_parent_email(self, student_id: int) -> tuple:
        # ... existing logic from NotificationService ...
        pass
    
    def _get_group_info(self, group_id: int) -> "GroupInfo":
        # ... fetch group + instructor info ...
        pass
    
    async def _dispatch(self, template, channel, recipient_id, contact, variables):
        # ... render template, call dispatcher, log result ...
        pass
```

### 4. Service Integration

```python
# app/modules/enrollments/services/enrollment_service.py

class EnrollmentService:
    def __init__(
        self,
        repo: EnrollmentRepository,
        event_bus: NotificationEventBus,  # Replace NotificationService
    ):
        self._repo = repo
        self._event_bus = event_bus
    
    def enroll_student(self, dto: EnrollStudentDTO) -> EnrollmentDTO:
        # ... validation and creation logic ...
        
        enrollment = self._repo.create(...)
        
        # Emit event (notification happens async)
        self._event_bus.publish(EnrollmentCreatedEvent(
            student_id=enrollment.student_id,
            enrollment_id=enrollment.id,
            group_id=enrollment.group_id,
            level_number=enrollment.level_number,
            enrolled_at=enrollment.enrolled_at,
            performed_by=dto.created_by,
        ))
        
        return EnrollmentDTO.model_validate(enrollment)
```

### 5. Bootstrap Registration

```python
# app/api/dependencies.py
from app.modules.notifications.events.event_bus import NotificationEventBus
from app.modules.notifications.handlers.enrollment_handler import EnrollmentNotificationHandler
from app.modules.notifications.handlers.payment_handler import PaymentNotificationHandler

# Create singleton bus
_event_bus = NotificationEventBus()

# Register handlers (called once at startup)
def _register_notification_handlers():
    # Initialize with dependencies
    enrollment_handler = EnrollmentNotificationHandler(
        repo=NotificationRepository(...),
        email_dispatcher=GmailEmailDispatcher(),
        whatsapp_dispatcher=TwilioWhatsAppDispatcher(),
    )
    
    # Subscribe to events
    _event_bus.subscribe(EnrollmentCreatedEvent, enrollment_handler.handle)
    _event_bus.subscribe(EnrollmentCompletedEvent, enrollment_handler.handle)
    _event_bus.subscribe(EnrollmentDroppedEvent, enrollment_handler.handle)
    _event_bus.subscribe(EnrollmentTransferredEvent, enrollment_handler.handle)
    
    # Payment handler
    payment_handler = PaymentNotificationHandler(...)
    _event_bus.subscribe(PaymentReceivedEvent, payment_handler.handle)
    
    logger.info("Notification handlers registered")

# Call on startup
_register_notification_handlers()

def get_event_bus() -> NotificationEventBus:
    """FastAPI dependency for event bus."""
    return _event_bus
```

---

## Comparison Matrix

| Criterion | Current | Strategy | Event-Driven | Chain | Factory |
|-----------|---------|----------|--------------|-------|---------|
| **Decoupling** | Poor | Good | Excellent | Good | Fair |
| **Extensibility** | Poor | Excellent | Excellent | Good | Fair |
| **Testability** | Poor | Excellent | Good | Good | Good |
| **Complexity** | Low | Medium | High | Medium-High | Medium |
| **Scalability** | Poor | Good | Excellent | Fair | Good |
| **Debuggability** | Good | Good | Fair | Poor | Good |
| **Learning Curve** | Low | Medium | High | Medium | Medium |
| **Codebase Fit** | N/A | Good | Excellent | Poor | Poor |

---

## Decision

**Recommended: Hybrid Event-Driven + Strategy Pattern**

### Why This Combination?

1. **Event-Driven solves the core problem**: Business services are 100% decoupled from notifications
2. **Strategy Pattern keeps it manageable**: Each notification type has clear, testable implementation
3. **Preserves existing infrastructure**: Current dispatchers (Email, WhatsApp) work unchanged
4. **Natural for scheduled reports**: Cron jobs just emit events
5. **Supports future channels**: Add Push, SMS by extending dispatchers
6. **Python-friendly**: No complex inheritance, uses composition + protocols

### Migration Strategy

```
Week 1: Foundation
  ├─ Create event bus and domain events
  ├─ Define handler protocol
  └─ Create first handler (enrollment)

Week 2: Migration
  ├─ Migrate existing notification methods to handlers
  ├─ Update service dependencies
  └─ Add tests for handlers

Week 3: Enhancement
  ├─ Add attendance handler
  ├─ Add payment reminder handler
  └─ Add retry/dead letter queue
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Event loss on crash | Persist events to DB before processing |
| Handler failure | Try/catch isolation + retry queue |
| Memory leak | Weak reference handlers + cleanup |
| Testing complexity | In-memory event bus for tests |
| Debugging difficulty | Structured logging + correlation IDs |

---

## Conclusion

The **Hybrid Event-Driven + Strategy Pattern** provides:
- ✅ Clean separation of concerns
- ✅ Easy extensibility for new notification types
- ✅ Decoupled domain logic from notification infrastructure
- ✅ Maintainable, testable code structure
- ✅ Foundation for future scalability (queue workers, retries)

**Next Step:** Confirm this direction, then begin Phase 1 implementation.
