---
status: accepted
---

# A Protocol/ABC exists only where two adapters satisfy it

There were 37 Protocol/ABC classes:
- 16 had zero references: every `interface.py` in academics and enrollments.
- The finance and crm `I*` interfaces each had exactly one implementation.

They doubled the files an agent or human must read without letting anything vary. An interface is kept only where at least two adapters exist, and a test fake counts as one. Today that is `IMessageDispatcher` (email, WhatsApp), `ReportDeliveryLedgerInterface` (SQL ledger, `InMemoryReportDeliveryLedger` fake) and `NotificationRepositoryInterface` (SQL repository, `MockNotificationRepository` fake), plus the Notifier ports (ADR-0007). Protocols are structural, so count fakes that satisfy them without subclassing. Every other interface is deleted. Callers and type hints use the concrete class. When a second adapter genuinely appears, introduce the interface then.
