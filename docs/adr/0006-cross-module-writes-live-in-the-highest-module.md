---
status: accepted
---

# A write workflow spanning modules lives in the highest module involved

Two single-transaction workflows called upward against the module order (ADR-0003):
- competitions' `TeamService.pay_competition_fee` and `refund_competition_fee` create receipts and refunds through finance.
- academics' `progress_to_next_level` migrates enrollments through enrollments.

Each workflow moves to the highest module it touches, which is also the module that owns the record it produces. Paying or refunding a competition fee becomes a finance use case that reads the team member through the competitions facade. Group level progression with enrollment migration becomes an enrollments use case that asks academics to create the level. Endpoints move to that module's `api/` with the same paths, because the API contract is frozen.

## Considered Options

- **A port per upward call** (for example a `FeeCharger` defined by competitions and implemented by finance): rejected. Each would add an interface for a core step of one transaction. Ports are reserved for after-commit side effects triggered from many modules (ADR-0007).
- **A top-level `app/workflows/` layer**: rejected. It adds a second place to look and tends to become a catch-all.
