# What counts as "delivered"

Type: grilling
Status: resolved
Blocked by:

## Question

For deciding whether to skip or retry, when does a report count as sent?

## Answer

Each **Delivery** is keyed on **(report type, report period, recipient)**:

- Recipients already `SENT` for that period are skipped.
- Recipients that `FAILED` are retried.
- Backfills for earlier periods are allowed.

This replaces the in-progress rule "any SENT row since midnight Cairo" (`internal_scheduler_router.py:57`), which blocked backfills and hid partial failures.

This requires the report period to be recorded on each delivery. Today `notification_logs` only has `created_at`. Ticket 09 decides how to store it.

Resolved 2026-09-25, while charting the map.
