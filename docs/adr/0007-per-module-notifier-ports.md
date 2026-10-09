---
status: accepted
---

# Modules notify through their own Notifier ports, never NotificationService

finance, enrollments, tasks and competitions imported `NotificationService` directly, while notifications imported seven modules back. Services also took FastAPI's `BackgroundTasks` as a parameter, which tied them to HTTP; cron paths passed `None` and silently skipped notifications. Each module that emits notifications now defines a small port with 2–5 methods in its own package, for example `EnrollmentNotifier.enrollment_created(...)`. notifications, at the top of the order, implements every port. A use case calls its notifier after `uow.commit()`. The adapter decides how to dispatch: HTTP dependencies build it with the request's `BackgroundTasks`, and cron and the scheduler build one that sends inline. Services no longer take a `BackgroundTasks` argument.

## Consequences

- Each port has a real adapter and a test fake, which meets the interface policy (ADR-0008).
- The `NotificationService` pass-through facade is deleted.
- Adapters live in `app/modules/notifications/adapters/`. **They are wired in the composition root, `create_app()` in `app/api/main.py`, never by the emitting module.** Each emitting module's `api/deps.py` declares a provider such as `get_enrollment_notifier()` that raises `NotImplementedError`, and `create_app()` sets `app.dependency_overrides[...]` to the notifications adapter factory. The lifespan builds the inline adapters for the scheduler the same way. This keeps lower modules from importing notifications, even indirectly through `app.api`, which import-linter's layer contract would flag.
