# Miss / failure detection

Type: grilling
Status: resolved
Blocked by:

## Question

The old watchdog ran inside the same process it was meant to watch, so it went down together with it. What should detect a missed or failed report, from outside the app?

## Answer

Use **Logfire alerts only.** No Healthchecks.io.

- Alerts are SQL queries over Logfire records, run on a schedule. The "starts or stops having results" mode lets an alert fire when an expected event is missing.
- This covers two cases: a report that never ran (no event), and SMTP failures across every notification.
- Open follow-ups: which channels and plan limits apply (ticket 12), and the exact rules and events (ticket 13).

Resolved 2026-09-25, while charting the map. The user saw a comparison with a Healthchecks.io dead-man's switch before choosing.
