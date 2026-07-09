# Spec 035 — Business Reports Feature

**Status:** DRAFT — open for discussion  
**Date:** 2026-07-09  
**Relates to:** `AGENTS.md § Techno Kids — Business Reports Context Document`

---

## 1. Problem Statement

The Techno Kids platform has accumulated two months of transactional data across students, enrollments, payments, group levels, and instructors. The operations team currently has **zero API visibility** into key business health signals from this data. Four specific reports have been validated against the live database and are ready to be built into the API surface.

Additionally, the business reports philosophy needs to be established: how should this system approach data extraction from its evolving schema in a way that is honest, maintainable, and avoids building false precision on top of dirty or incomplete data?

---

## 2. Philosophy: Honest Reporting from an Evolving Schema

### 2.1 — Data Fidelity Over Vanity

Every report must be honest about the **quality of its underlying data**. The schema has evolved faster than its usage, leaving orphaned nulls (`waiting_since`), bulk-imported records, and partially backfilled foreign keys (`group_levels.instructor_id`). A report that silently papers over these gaps will mislead decision-makers.

**Design rule:** Any report built on incomplete data must either:
- (a) Exclude the bad data and say so (filter + `data_note`), or
- (b) Fall back to a proxy column and say so (COALESCE with documentation), or
- (c) Block at the endpoint level and surface an actionable error to the caller.

### 2.2 — Temporal Anchoring

The system has been live since May 2026. Reports that make claims like "12-month retention" or "year-over-year growth" will return zero results or misleading comparisons. All reports must:
- Introspect the actual data range before applying any threshold-based logic.
- Use `MIN(enrolled_at)` / `MIN(created_at)` as a dynamic anchor instead of hard-coded dates.
- The `OLD_CUSTOMERS_CUTOFF` (currently `2026-06-01`) should be a **computed constant** derived from the first month of data, not a hard-coded literal in source code.

### 2.3 — Schema Lag: Always Query Live

As documented in AGENTS.md, the actual live schema diverges from any written document. The system must not add a "schema version" abstraction. Instead:
- All report queries live in repositories and use raw `text()` SQL — keeping queries grounded in the real schema.
- The analytics module already follows this pattern (`bi_repository.py`, `financial_repository.py`).
- New report queries follow the same: one function per report, one DTO per output row shape.

### 2.4 — Reports vs. BI: Two Different Beasts

The existing `analytics/` module contains two distinct categories that should remain separate:

| Category | Purpose | Pattern | Examples (existing) |
|---|---|---|---|
| **BI Analytics** | Internal dashboards, trend analysis, risk signals | Stateless, open-ended, filterable | `bi_repository.py`, `financial_repository.py` |
| **Business Reports** | Defined, named, answerable questions for operations | Fixed shape, documented logic, named reports | **New — this spec** |

Business Reports have a **contract**: the same report run twice should produce a consistent interpretation. BI analytics can be exploratory. This distinction must be maintained in the API namespace (`/analytics/reports/` vs `/analytics/bi/`).

---

## 3. The Four Reports — Technical Design

### Report 1 — New Customers

**Endpoint:** `GET /analytics/reports/new-customers`  
**Question:** How many students registered each month?

**Data source:** `students.created_at`, soft-delete filtered.

```sql
SELECT date_trunc('month', created_at)::date AS month, count(*) AS new_customers
FROM students
WHERE deleted_at IS NULL
GROUP BY 1
ORDER BY 1;
```

**DTO:**
```python
class NewCustomersRowDTO(BaseModel):
    month: date
    new_customers: int
```

**Data quality:** Clean. `created_at` is reliably populated on insert. No known nulls.

---

### Report 2 — Old Customers

**Endpoint:** `GET /analytics/reports/old-customers`  
**Question:** Which students have been with us since the earliest cohort?

**Data source:** `students` JOIN `enrollments`. Threshold: `MIN(enrolled_at) < cutoff`.

**Dynamic cutoff logic** (computed, not hard-coded):
```sql
SELECT date_trunc('month', MIN(enrolled_at))::date + INTERVAL '1 month'
FROM enrollments;
-- Returns start of the second month of data = 2026-06-01 currently
```

**Query:**
```sql
SELECT s.id, s.full_name, s.phone, MIN(e.enrolled_at) AS first_enrollment
FROM students s
JOIN enrollments e ON e.student_id = s.id
WHERE s.deleted_at IS NULL
GROUP BY s.id, s.full_name, s.phone
HAVING MIN(e.enrolled_at) < :cutoff
ORDER BY first_enrollment;
```

**DTO:**
```python
class OldCustomerRowDTO(BaseModel):
    id: int
    full_name: str
    phone: Optional[str]
    first_enrollment: datetime

class OldCustomersReportDTO(BaseModel):
    cutoff_date: date       # active threshold — shows caller what "old" means today
    customer_count: int
    rows: list[OldCustomerRowDTO]
```

**Data quality:** ⚠️ Cutoff definition changes as history grows. The `cutoff_date` field in the response ensures the caller always knows what definition was applied.

---

### Report 3 — New Waiting Students (Monthly)

**Endpoint:** `GET /analytics/reports/waiting-monthly`  
**Question:** How many new students entered the waiting list each month?

**Current status: DATA QUALITY ISSUE — requires an app fix first.**

`waiting_since` is NULL for all 303 existing waiting students. The app never sets it on status transition.

**Two-phase delivery:**
- **Phase A (prerequisite):** App fix — set `waiting_since = now()` when `status` is set to `'waiting'`. Lives in CRM service layer (business rule, not repository).
- **Phase B (this spec):** Build the endpoint with a data-quality transparency flag. The report runs regardless but surfaces the count of rows that fell back to `created_at`.

**Query:**
```sql
SELECT
    date_trunc('month', COALESCE(waiting_since, created_at))::date AS month,
    count(*) AS new_waiting,
    count(*) FILTER (WHERE waiting_since IS NULL) AS missing_waiting_since
FROM students
WHERE status = 'waiting' AND deleted_at IS NULL
GROUP BY 1
ORDER BY 1;
```

**DTO:**
```python
class WaitingMonthlyRowDTO(BaseModel):
    month: date
    new_waiting: int
    missing_waiting_since: int  # rows that fell back to created_at

class WaitingMonthlyReportDTO(BaseModel):
    data_quality_warning: bool  # True if any rows are missing waiting_since
    total_missing: int
    rows: list[WaitingMonthlyRowDTO]
```

---

### Report 4 — Round Cost

**Endpoint:** `GET /analytics/reports/round-cost`  
**Question:** For each group level taught by a contract instructor, what was the instructor's earned cost?

**Scope:** Contract instructors only. Part-time salary allocation is out of scope.

**Query:**
```sql
WITH level_revenue AS (
  SELECT gl.id AS group_level_id, gl.group_id, gl.level_number,
         COALESCE(gl.instructor_id, g.instructor_id) AS instructor_id,
         COALESCE(SUM(p.amount), 0) AS revenue_collected
  FROM group_levels gl
  JOIN groups g ON g.id = gl.group_id
  LEFT JOIN enrollments e ON e.group_id = gl.group_id AND e.level_number = gl.level_number
  LEFT JOIN payments p ON p.enrollment_id = e.id AND p.deleted_at IS NULL AND p.transaction_type = 'payment'
  GROUP BY gl.id, gl.group_id, gl.level_number, COALESCE(gl.instructor_id, g.instructor_id)
)
SELECT lr.group_level_id, c.name AS course, lr.level_number, emp.full_name AS instructor,
       lr.revenue_collected, emp.contract_percentage,
       ROUND(lr.revenue_collected * emp.contract_percentage / 100, 2) AS round_cost
FROM level_revenue lr
JOIN groups g ON g.id = lr.group_id
JOIN courses c ON c.id = g.course_id
JOIN employees emp ON emp.id = lr.instructor_id
WHERE emp.employment_type = 'contract'
ORDER BY lr.group_level_id;
```

**DTO:**
```python
class RoundCostRowDTO(BaseModel):
    group_level_id: int
    course: str
    level_number: int
    instructor: str
    revenue_collected: float
    contract_percentage: float
    round_cost: float
```

**Data quality notes:**
- ⚠️ Rounds where both `group_levels.instructor_id` and `groups.instructor_id` are NULL are silently excluded. The COALESCE fallback is explicit in the query.
- Currently no `'refund'` rows exist; as the system matures, refunds will naturally reduce `revenue_collected` (the query already handles this correctly via `transaction_type = 'payment'` filter).

---

## 4. API Surface

### Namespace

```
GET /analytics/reports/new-customers
GET /analytics/reports/old-customers
GET /analytics/reports/waiting-monthly
GET /analytics/reports/round-cost
```

Distinct from: `/analytics/bi/*` (exploratory) and `/analytics/finance/*` (financial metrics).

### Auth

All four: `require_admin` — consistent with all existing analytics endpoints.

### Optional Parameters (TBD)

| Endpoint | Proposed optional params |
|---|---|
| `new-customers` | None |
| `old-customers` | `cutoff_date` override? (open question) |
| `waiting-monthly` | None |
| `round-cost` | `instructor_id`? `course_id`? |

---

## 5. Implementation Architecture

### Module layout

```
app/modules/analytics/
├── repositories/
│   └── reports_repository.py      ← NEW: 4 report query functions
├── services/
│   └── reports_service.py         ← NEW: thin service orchestration
└── schemas/
    └── business_reports_schemas.py ← NEW: DTOs for all 4 reports

app/api/routers/analytics/
└── reports.py                     ← NEW: 4 GET endpoints

app/modules/crm/services/          ← MODIFY: waiting_since fix (Phase A)
app/api/dependencies.py            ← ADD: get_business_reports_service()
```

### Why separate from `reports_schemas.py`?

The existing `reports_schemas.py` is for **operational push reports** (daily, weekly, attendance, competition — sent via notification pipeline). The new business reports are **pull-style management reports** with a fundamentally different contract and lifecycle. They must not be intermixed.

### DI Pattern

Analytics module uses stateless pattern: services open their own `get_session()` per call. The new `BusinessReportsService` follows the same pattern (no UoW, no session injection).

---

## 6. Open Questions for Discussion

1. **`old-customers` cutoff:** Should the cutoff be fully dynamic (derived from live data every call), or allow an optional `cutoff_date` query param override? Dynamic is safer but opaque to the caller.

2. **`round-cost` filters:** Ship flat (full table) first, or add optional `instructor_id`/`course_id` filters from day one?

3. **`waiting_since` fix scope:** Should the CRM fix be part of this spec (035) or a dedicated micro-spec (036) to keep scopes clean?

4. **Postgres views:** Create `v_new_customers`, `v_old_customers`, etc. as formal migrations? Pro: documents the query contract. Con: adds migration artifact and indirection during a still-evolving schema. Recommendation: keep as inline SQL for now, revisit when queries are stable.

5. **`ReportMeta` wrapper:** Should all four reports share a common `ReportMeta` envelope (with `generated_at`, `data_note`, `data_quality_warning`) for consistency with the existing `reports_schemas.ReportMeta`? Or is per-report DTO flexibility more valuable?

6. **Frontend scope:** Will the UI consume these endpoints immediately, or is this backend-only for now?

---

## 7. Out of Scope

- Part-time instructor cost report (separate spec, not yet designed).
- Report scheduling / push notifications (existing notification module handles this).
- CSV/Excel export.
- Dashboard caching or background pre-computation.
- Any write operations — these are read-only reporting endpoints.
