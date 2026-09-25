# Request timeout and background-work limits

Type: research
Status: resolved
Blocked by:

## Question

1. What is the maximum request duration for an app on FastAPI Cloud? That includes the Cloudflare proxy in front of it; Cloudflare's usual cutoff is 100s.
2. Does work continue after the response (FastAPI `BackgroundTasks`), or does it get killed when the app scales down after going idle?
3. What is the highest `timeout_milliseconds` `pg_net` accepts?

Cite primary sources.

## Answer

The full findings, with citations, are in `.scratch/reliable-report-delivery/research/07-request-timeout-limits.md` on the branch `research/07-request-timeout-limits` (commit `bdc9ec5`).

1. **Maximum request duration is unknown. It could be anywhere from 15s to 125s.**
   - FastAPI Cloud doesn't document one.
   - A live check of the headers shows Cloudflare in front of an Envoy proxy.
   - Cloudflare cuts off at 125s and returns a 524. Only Enterprise can raise that.
   - Envoy's default route timeout is 15s. FastAPI Cloud's Envoy settings aren't documented.
2. **Work after the response is best-effort.** How idle is detected, how replicas are drained and the SIGTERM grace period are all undocumented, and scale-to-zero is on by default. `BackgroundTasks` and `create_task` work may be killed partway through. That last point is an inference, not documented.
3. **`pg_net`: no practical cap on `timeout_milliseconds`** in the versions Supabase ships. The source default is 5000 ms; the docs say 2000.
   - A timeout is recorded as `timed_out=true` with a NULL status.
   - A proxy 524 is recorded as `status_code=524`.
   - Rows expire after 6 hours.

**What this means for the map:** the platform cutoff has to be measured before ticket 08 can be decided. That measurement is ticket 17.

Resolved 2026-09-25 by a research subagent.
