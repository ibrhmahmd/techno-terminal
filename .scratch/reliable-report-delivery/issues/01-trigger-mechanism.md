# Trigger mechanism

Type: grilling
Status: resolved
Blocked by:

## Question

The in-process `while True` loop can't fire while FastAPI Cloud has scaled the app to zero, which is the default and can't be changed on Hobby. It also fires once per replica. What should trigger the scheduled reports instead?

## Answer

Use **Supabase `pg_cron` + `pg_net`**: a scheduled `net.http_post` to an authenticated internal endpoint.

- Chosen over Upstash QStash (a new vendor), cron-job.org (gives up after 30s) and FastAPI Cloud Pro with min replicas ≥1 (still duplicates with several replicas).
- Constraints to carry forward: `pg_net`'s timeout defaults to 2000 ms and has to be raised. `pg_net` doesn't retry. Responses stay in `net._http_response` for only 6 hours.
- Evidence: production `notification_logs` show daily reports only on 8/24, 8/31, 9/03 and 9/04, nothing at all after 9/04, and 3 duplicate sends on 8/31.

Resolved 2026-09-25, while charting the map.
