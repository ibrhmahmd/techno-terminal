# Schedule shape, send time and timezone

Type: grilling
Status: resolved
Blocked by:

## Question

Should there be one daily trigger that works out which reports are due (daily always, weekly on Monday, monthly on the 1st)? Or three separate `pg_cron` jobs?

- At what Cairo time should reports go out? The old window was about 01:31–02:00.
- `pg_cron` schedules in UTC, and Egypt observes DST. How do we keep the Cairo send time right across DST changes?

## Answer

Three `pg_cron` jobs, one per report type (daily; weekly on Monday; monthly on the 1st), at **05:00 UTC**. That's 08:00 Cairo in summer and 07:00 in winter; the one-hour DST shift is accepted. Default accepted by the user on 2026-09-25.
