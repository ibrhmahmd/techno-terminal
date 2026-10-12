---
status: accepted
---

# finance operates, analytics analyses, audit verifies; the SQL views are the source of truth for aggregates

Money figures were computed in four places: finance's reporting and balance reads, analytics' financial and BI endpoints, the dashboard's 12 `v_finance_*` and 23 `v_bi_*` views, and the notifications reports. Several overlap (revenue by method, outstanding balances and debtors, monthly revenue), so the same number can disagree between screens. We decided a single responsibility rule:

- **finance** owns money writes and the day-to-day reads needed to do the work: one student's balance, today's collections and receipts, the lists to chase.
- **analytics** owns every aggregate, trend and KPI across modules, including the finance and BI views.
- **audit** owns integrity checks only: finding invalid records (scenarios A–I), their severity and counts. It never computes KPIs.

For aggregates, **the SQL views are the single source of truth**: repositories `SELECT` from them, and duplicated aggregate queries are deleted.

## Consequences

- #115 exposes the finance and BI views through analytics endpoints and removes the overlapping queries; the demo UI then reads them through analytics.
- The notifications reports compute their own figures because notifications sits below analytics; #116 moves the report workflow into analytics (ADR-0006), after #37.
- `db/schema.sql` must contain every view the code reads, so a database built from it matches production (the reporting views live in `db/schema/45_reporting_views.sql`).
