# What to do with the in-progress code

Type: grilling
Status: resolved
Blocked by: 08, 09

## Question

The uncommitted work consists of:
- `internal_scheduler_router.py` and `tests/test_internal_scheduler.py`
- removing the lifespan scheduler and the watchdog
- the `smtp_auth_failed` Logfire event

Should it be reworked to match the decisions on this map, or discarded and rebuilt from the spec? In what order should it ship?

Also: the recipient address change (`ibrahim.ahmd.net` → `techno.terminal.notifications`) should go in its own commit.

## Answer

Rework the in-progress code in place; it's delegated to OpenCode together with the brief for 08, 09 and 10. The recipient-address change stays separate. Default accepted by the user on 2026-09-25.
