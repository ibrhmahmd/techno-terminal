# Measure how long a report run takes

Type: task
Status: resolved
Blocked by:

## Question

AFK. How long do `send_daily_report`, `send_weekly_report` and `send_monthly_report` take from start to finish?

- Run them against the testing project with SMTP stubbed, and time aggregates + PDF + render separately from the send.
- Estimate per-recipient SMTP time.

Record p50 and worst-case durations. Ticket 08 needs these numbers to decide whether a synchronous request fits within the caller and proxy timeouts.

## Answer

**How it was measured.** The harness is `research/06-time_reports.py`, run from a dev machine against the testing project (`qugffjtucavdseczbata`). SMTP was stubbed out, and `_dispatch` was replaced with a timer that only renders, so no emails were sent and no logs were written. The testing project has **no report templates**, so production's 3 template rows were read read-only and injected in memory. Dates used: daily 2026-07-25, weekly 07-20–07-26, monthly July; the testing data stops at 07-26. Each report ran 4 times. Times are in seconds.

| Phase | Daily | Weekly | Monthly |
|---|---|---|---|
| Recipient lookup (first DB round trips) | cold **13.8**, warm 0.6–1.3 | 1.5–1.8 | 0.9–2.4 |
| Aggregate SQL | 3.0–4.7 | 3.4–4.5 | 3.7–6.5 |
| PDF + building variables + rendering | ≈0.05 | ≈0 | ≈0 |
| **Generation total** | **cold 18.0, warm 3.6–6.0** | 4.9–6.1 | 4.6–8.9 |

- **Per recipient, SMTP only:** Gmail `SMTP_SSL` connect + login takes 1.5–2.9s, median **2.35s**, measured 5 times with nothing sent. The dispatcher opens a **new SMTP connection for each recipient**, one after another (`email_dispatcher.py:88`). It also writes 2 log rows per recipient. So estimate about **3–3.5s per recipient**.
- **Estimated end-to-end for a trigger:**
  - Production today (1 recipient): daily is about **9s warm and 22s cold**.
  - A Monday (daily + weekly in one run): about 18–30s.
  - The 1st of the month when it's also a Monday: about 27–40s.
  - Each extra recipient adds about 3.5s. The testing data has 19 daily recipients, which would take about 70–85s.
- **Caveats:**
  - Latency from the dev machine to Supabase differs from FastAPI Cloud's. Production's pooler is `aws-1-eu-north-1`; the app's region is unknown.
  - The FastAPI Cloud cold start after scale-to-zero comes on top and wasn't measured.

**What this means for ticket 08:**
- One warm daily report for one recipient fits inside even a 15s cutoff.
- A cold start, or several reports in one request, does **not** fit a 15s cutoff. It might fit 125s.
- Time grows with the number of recipients and with sending one after another.
- So ticket 17's measured cutoff decides whether the synchronous option is viable. Another option to consider in 08: one Trigger per report type, or per recipient.

**Side findings:**
- The testing project has no `daily_report`, `weekly_report` or `monthly_report` templates, and 0 weekly recipients. The rollout path (ticket 11) must seed these before running end-to-end tests on testing.
- Recipient resolution opens a new session for each query, which makes it slow on a cold start.

Resolved 2026-09-25.
