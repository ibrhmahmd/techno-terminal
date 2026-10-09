---
status: accepted
---

# One injected Unit of Work per use case; only the top-level use case commits

A single request used to open 3–5 database sessions. `enroll_student`, for example, wrote the enrollment in one transaction and its activity log in another, so one could commit while the other failed, and the request held several pool connections at once. Services also mixed two models: a request-scoped UoW for CRM, Finance and HR, and services opening their own `get_session()` everywhere else (129 call sites). We decided that every service and repository receives one app-wide `UnitOfWork` (`app/db/uow.py`, which wraps a single `Session`). Services never open sessions. Only the outermost use case calls `uow.commit()`, and it does so before any external I/O (Supabase, PDF rendering, email). HTTP builds the UoW in `get_uow` with `Depends(..., scope="function")`, so a failed commit becomes an error response rather than a 200 already sent. Cron triggers, the tasks scheduler and tests build the same object with `with unit_of_work() as uow:`. Tests bind it to an outer transaction and roll that back, so they leave no rows behind.

## Considered Options

- **Request-scoped session committed by `get_db`**: rejected. The commit point is hidden in DI, it works only for HTTP, and with FastAPI's default request scope it commits after the response is sent.
- **Use-case-owned UoW without injection**: rejected. It regresses as soon as one collaborator opens its own session again, and tests have to patch `get_session`.
- **Ambient contextvar session**: rejected. It is cheapest to migrate to, but it is a hidden global, and background tasks run after the request context is closed.

## Consequences

- A test fails if `get_session()` appears under `app/modules`.
- Notification background tasks still open their own session, because they run after the request has finished. This is the one sanctioned exception, and it lives inside the notifications adapter.
- Per-module UoWs (`StudentUnitOfWork`, `FinanceUnitOfWork`, `HRUnitOfWork`) are removed. Repositories are classes built from `uow.session`.
