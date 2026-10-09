---
status: accepted
---

# Any module may read any model, but writes only its own tables

Read views legitimately span modules. The student profile shows enrollments, payments and attendance, and group details show payments. Forbidding cross-module queries would force those views into a separate read layer, or into routers that call N facades per page. ORM models are therefore a shared layer beneath the module order (ADR-0003): any repository may SELECT or JOIN any model. INSERT, UPDATE and DELETE are allowed only on the module's own tables. A write to another module's table goes through that module's facade. A cross-module read view lives in the module that serves it, and it reads other models directly rather than calling upward services or repositories.

## Consequences

- Business calculations that already exist elsewhere (balances, attendance rates) are reused through the owning module's facade when that module is below. If it is above, the view moves up to that module rather than duplicating the calculation in SQL.
- Raw SQL (`text()`) is allowed only in repositories. `report_notifications.py` currently holds 27 queries and must move them into its repository.
